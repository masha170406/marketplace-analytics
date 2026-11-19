
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import MetaData, Table, insert, select, text

from database.connection import engine


NUMBER_OF_ORDERS = 8000
BATCH_SIZE = 1000

START_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

# Reserve enough time for an order to reach its final status
MAX_ORDER_LIFECYCLE_DAYS = 14

BUYER_FEE_RATE = Decimal("0.05")
SELLER_FEE_RATE = Decimal("0.05")
SHIPPING_FEE = Decimal("4.99")

CURRENCY = "EUR"

RANDOM_SEED = 42

ORDER_STATUS_PROBABILITIES = {
    "pending": 0.03,
    "awaiting_payment": 0.05,
    "paid": 0.04,
    "shipped": 0.05,
    "delivered": 0.05,
    "completed": 0.65,
    "cancelled": 0.10,
    "refunded": 0.03,
}

ORDER_STATUS_PATHS = {
    "pending": ["pending"],
    "awaiting_payment": ["pending", "awaiting_payment"],
    "paid": ["pending", "awaiting_payment", "paid"],
    "shipped": ["pending", "awaiting_payment", "paid", "shipped"],
    "delivered": [
        "pending",
        "awaiting_payment",
        "paid",
        "shipped",
        "delivered",
    ],
    "completed": [
        "pending",
        "awaiting_payment",
        "paid",
        "shipped",
        "delivered",
        "completed",
    ],
    "cancelled": ["pending", "awaiting_payment", "cancelled"],
    "refunded": [
        "pending",
        "awaiting_payment",
        "paid",
        "refunded",
    ],
}


def money(value):
    """Round a value to two decimal places."""
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def ensure_utc(value):
    """Ensure a datetime is timezone-aware."""
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def load_tables(connection):
    """Reflect the database tables."""
    metadata = MetaData()

    table_names = [
        "users",
        "listings",
        "listing_statuses",
        "listing_status_history",
        "orders",
        "order_items",
        "order_statuses",
        "order_status_history",
    ]

    tables = {}

    for table_name in table_names:
        tables[table_name] = Table(
            table_name,
            metadata,
            autoload_with=connection,
        )

    return tables


def load_order_statuses(connection, table):
    rows = connection.execute(
        select(
            table.c.order_status_id,
            table.c.status_name,
        )
    ).mappings().all()

    statuses = {
        row["status_name"]: row["order_status_id"]
        for row in rows
    }

    required = set(ORDER_STATUS_PATHS.keys())
    missing = required - set(statuses.keys())

    if missing:
        raise ValueError(
            f"Missing order statuses in order_statuses table: {missing}"
        )

    return statuses


def load_listing_statuses(connection, table):
    rows = connection.execute(
        select(
            table.c.listing_status_id,
            table.c.status_name,
        )
    ).mappings().all()

    statuses = {
        row["status_name"]: row["listing_status_id"]
        for row in rows
    }

    required = {"active", "sold", "reserved"}

    missing = required - set(statuses.keys())

    if missing:
        raise ValueError(
            f"Missing listing statuses: {missing}"
        )

    return statuses


def load_buyers(connection, users_table):
    rows = connection.execute(
        select(users_table.c.user_id).where(
            users_table.c.account_status == "active"
        )
    ).scalars().all()

    return list(rows)


def load_eligible_listings(
    connection,
    listings_table,
    listing_statuses_table,
    listing_history_table,
    listing_status_ids,
):


    latest_history = (
        select(
            listing_history_table.c.listing_id,
            listing_history_table.c.listing_status_id,
            listing_history_table.c.changed_at,
        )
        .distinct(listing_history_table.c.listing_id)
        .order_by(
            listing_history_table.c.listing_id,
            listing_history_table.c.changed_at.desc(),
        )
        .subquery()
    )

    query = (
        select(
            listings_table.c.listing_id,
            listings_table.c.seller_id,
            listings_table.c.price,
            listings_table.c.currency,
            listings_table.c.published_at,
            listings_table.c.listing_status_id,
            listing_statuses_table.c.status_name.label("status_name"),
            latest_history.c.listing_status_id.label(
                "latest_history_status_id"
            ),
            latest_history.c.changed_at.label("latest_history_at"),
        )
        .join(
            listing_statuses_table,
            listings_table.c.listing_status_id
            == listing_statuses_table.c.listing_status_id,
        )
        .outerjoin(
            latest_history,
            listings_table.c.listing_id == latest_history.c.listing_id,
        )
        .where(
            listing_statuses_table.c.status_name.in_(["active", "sold"]),
            listings_table.c.published_at.is_not(None),
        )
    )

    rows = connection.execute(query).mappings().all()

    eligible = []

    order_cutoff = END_DATE - timedelta(
        days=MAX_ORDER_LIFECYCLE_DAYS
    )

    for row in rows:
        listing = dict(row)

        published_at = ensure_utc(listing["published_at"])
        latest_history_at = ensure_utc(
            listing["latest_history_at"]
        )

        if published_at is None:
            continue

        if published_at < START_DATE or published_at > order_cutoff:
            continue

        listing["published_at"] = published_at
        listing["latest_history_at"] = latest_history_at

        if listing["status_name"] == "sold":
            # The latest event must confirm that the listing was sold
            if listing["latest_history_status_id"] != listing_status_ids["sold"]:
                continue

            if latest_history_at is None:
                continue

            # The generated order must finish before the original sale event
            listing["order_end_date"] = min(
                order_cutoff,
                latest_history_at - timedelta(
                    days=MAX_ORDER_LIFECYCLE_DAYS
                ),
            )

        else:
            # For active listings, the latest history timestamp is not an upper date boundary
            listing["order_end_date"] = order_cutoff

        if listing["order_end_date"] <= published_at:
            continue

        eligible.append(listing)

    return eligible


# ORDER DATE GENERATION

def generate_order_date(listing):
    published_at = listing["published_at"]
    end_date = listing["order_end_date"]

    if published_at >= end_date:
        raise ValueError(
            f"Invalid date range for listing {listing['listing_id']}: "
            f"published_at={published_at}, end_date={end_date}"
        )

    start_timestamp = published_at.timestamp()
    end_timestamp = end_date.timestamp()

    return datetime.fromtimestamp(
        random.uniform(start_timestamp, end_timestamp),
        tz=timezone.utc,
    )


# ORDER STATUS AND TIMELINE

def choose_order_status():
    statuses = list(ORDER_STATUS_PROBABILITIES.keys())
    probabilities = list(ORDER_STATUS_PROBABILITIES.values())

    return random.choices(
        statuses,
        weights=probabilities,
        k=1,
    )[0]


def generate_order_history(
    order_id,
    final_status,
    order_date,
    order_status_ids,
):
    """
    Generate a chronological order status history.

    Returns:
        history_records
        final_event_timestamp
    """

    status_path = ORDER_STATUS_PATHS[final_status]

    current_time = order_date
    history_records = []

    for index, status_name in enumerate(status_path):
        if index > 0:
            current_time += timedelta(
                hours=random.randint(2, 24)
            )

        history_records.append({
            "order_id": order_id,
            "order_status_id": order_status_ids[status_name],
            "changed_at": current_time,
            "change_reason": (
                "Order created"
                if index == 0
                else f"Order status changed to {status_name}"
            ),
        })

    return history_records, current_time


# GENERATE ORDER RECORDS

def generate_order_records(listings, buyers):
    if len(listings) < NUMBER_OF_ORDERS:
        raise ValueError(
            f"Not enough eligible listings. "
            f"Required: {NUMBER_OF_ORDERS}, "
            f"Available: {len(listings)}"
        )

    if not buyers:
        raise ValueError("No active buyers found.")

    selected_listings = random.sample(
        listings,
        NUMBER_OF_ORDERS,
    )

    order_records = []
    order_listing_data = []

    for listing in selected_listings:
        seller_id = listing["seller_id"]

        # Select a buyer different from the seller
        buyer_id = random.choice(buyers)

        while buyer_id == seller_id:
            buyer_id = random.choice(buyers)

        order_date = generate_order_date(listing)

        # Existing sold listings represent completed historical sales
        if listing["status_name"] == "sold":
            final_status = "completed"
        else:
            final_status = choose_order_status()

        item_price = money(listing["price"])

        buyer_fee = money(
            item_price * BUYER_FEE_RATE
        )

        seller_fee = money(
            item_price * SELLER_FEE_RATE
        )

        total_amount = money(
            item_price + buyer_fee + SHIPPING_FEE
        )

        order_records.append({
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "order_status_id": None,
            "item_subtotal": item_price,
            "buyer_fee": buyer_fee,
            "seller_fee": seller_fee,
            "shipping_fee": SHIPPING_FEE,
            "total_amount": total_amount,
            "currency": listing["currency"] or CURRENCY,
            "created_at": order_date,
            "completed_at": None,
            "cancelled_at": None,
        })

        order_listing_data.append({
            "listing_id": listing["listing_id"],
            "final_status": final_status,
            "item_price": item_price,
            "order_date": order_date,
            "listing_was_already_sold": (
                listing["status_name"] == "sold"
            ),
        })

    return order_records, order_listing_data


def insert_orders(
    connection,
    tables,
    order_records,
    order_listing_data,
    order_status_ids,
    listing_status_ids,
):
    orders_table = tables["orders"]
    order_items_table = tables["order_items"]
    order_history_table = tables["order_status_history"]
    listing_history_table = tables["listing_status_history"]
    listings_table = tables["listings"]

    inserted_orders = 0

    for batch_start in range(
        0,
        len(order_records),
        BATCH_SIZE,
    ):
        batch_end = min(
            batch_start + BATCH_SIZE,
            len(order_records),
        )

        order_batch = order_records[batch_start:batch_end]
        listing_batch = order_listing_data[batch_start:batch_end]

        order_ids = []
        order_item_records = []
        order_history_records = []
        listing_history_records = []
        listing_updates = []

        for record, listing_data in zip(
            order_batch,
            listing_batch,
        ):
            final_status = listing_data["final_status"]
            order_date = listing_data["order_date"]

            record["order_status_id"] = order_status_ids[final_status]

            # Generate order status history first, so completed_at and cancelled_at match the final status event
            history_records, final_event_time = generate_order_history(
                None,
                final_status,
                order_date,
                order_status_ids,
            )

            if final_status == "completed":
                record["completed_at"] = final_event_time

            elif final_status == "cancelled":
                record["cancelled_at"] = final_event_time

            # Insert the order and retrieve its generated ID
            result = connection.execute(
                insert(orders_table).values(**record).returning(
                    orders_table.c.order_id
                )
            )

            order_id = result.scalar_one()
            order_ids.append(order_id)

            # Add the order ID to each history row
            for history_record in history_records:
                history_record["order_id"] = order_id

            order_history_records.extend(history_records)

            # One listing per order
            order_item_records.append({
                "order_id": order_id,
                "listing_id": listing_data["listing_id"],
                "item_price": listing_data["item_price"],
                "created_at": order_date,
            })

            # Preserve pre-existing sold listings and their history
            if listing_data["listing_was_already_sold"]:
                continue

            # Update the listing after the order reaches its final state
            if final_status == "completed":
                new_listing_status = "sold"
                listing_event_time = final_event_time

            elif final_status in {
                "cancelled",
                "refunded",
            }:
                new_listing_status = "active"
                listing_event_time = final_event_time

            else:
                new_listing_status = "reserved"
                listing_event_time = order_date

            listing_updates.append({
                "listing_id": listing_data["listing_id"],
                "listing_status_id": listing_status_ids[
                    new_listing_status
                ],
            })

            listing_history_records.append({
                "listing_id": listing_data["listing_id"],
                "listing_status_id": listing_status_ids[
                    new_listing_status
                ],
                "changed_by_user_id": record["buyer_id"],
                "changed_at": listing_event_time,
                "change_reason": (
                    f"Listing status changed to {new_listing_status} "
                    f"after order {order_id}"
                ),
            })

        # Insert dependent records
        if order_item_records:
            connection.execute(
                insert(order_items_table),
                order_item_records,
            )

        if order_history_records:
            connection.execute(
                insert(order_history_table),
                order_history_records,
            )

        if listing_history_records:
            connection.execute(
                insert(listing_history_table),
                listing_history_records,
            )

        # Update the current listing status
        for update_record in listing_updates:
            connection.execute(
                listings_table.update()
                .where(
                    listings_table.c.listing_id
                    == update_record["listing_id"]
                )
                .values(
                    listing_status_id=update_record["listing_status_id"]
                )
            )

        inserted_orders += len(order_batch)

        print(
            f"Inserted {inserted_orders:,} / "
            f"{len(order_records):,} orders"
        )



def generate_orders():
    random.seed(RANDOM_SEED)

    print("Starting order generation...")

    with engine.begin() as connection:
        tables = load_tables(connection)

        # Prevent accidental duplicate generation.
        existing_orders = connection.execute(
            select(text("COUNT(*)")).select_from(
                tables["orders"]
            )
        ).scalar_one()

        if existing_orders > 0:
            raise ValueError(
                f"The orders table already contains "
                f"{existing_orders:,} rows. "
                "Order generation was stopped to prevent duplicates."
            )

        order_status_ids = load_order_statuses(
            connection,
            tables["order_statuses"],
        )

        listing_status_ids = load_listing_statuses(
            connection,
            tables["listing_statuses"],
        )

        buyers = load_buyers(
            connection,
            tables["users"],
        )

        listings = load_eligible_listings(
            connection,
            tables["listings"],
            tables["listing_statuses"],
            tables["listing_status_history"],
            listing_status_ids,
        )

        print(f"Available listings: {len(listings):,}")
        print(f"Available buyers: {len(buyers):,}")

        if len(listings) < NUMBER_OF_ORDERS:
            raise ValueError(
                f"Only {len(listings):,} eligible listings are available. "
                f"The generator requires {NUMBER_OF_ORDERS:,}."
            )

        records, order_listing_data = generate_order_records(
            listings,
            buyers,
        )

        print("Generating and inserting orders...")

        insert_orders(
            connection,
            tables,
            records,
            order_listing_data,
            order_status_ids,
            listing_status_ids,
        )

    print("Order generation completed successfully.")


if __name__ == "__main__":
    generate_orders()
