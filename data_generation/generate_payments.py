
import random
import uuid

from datetime import timedelta
from sqlalchemy import MetaData, Table, select, insert

from database.connection import engine

RANDOM_SEED = 42
BATCH_SIZE = 1000

PAYMENT_METHODS = [
    "card",
    "paypal",
    "apple_pay",
    "google_pay",
    "bank_transfer",
]

PAYMENT_METHOD_WEIGHTS = [
    0.50,
    0.20,
    0.12,
    0.10,
    0.08,
]

# Probability of an additional failed attempt before success
EXTRA_ATTEMPT_PROBABILITY = 0.20

# Probability of a failed attempt for an unpaid order
UNPAID_FAILURE_PROBABILITY = 0.65



def load_tables(connection):
    metadata = MetaData()

    payments = Table(
        "payments",
        metadata,
        autoload_with=connection,
    )

    orders = Table(
        "orders",
        metadata,
        autoload_with=connection,
    )

    order_statuses = Table(
        "order_statuses",
        metadata,
        autoload_with=connection,
    )

    payment_statuses = Table(
        "payment_statuses",
        metadata,
        autoload_with=connection,
    )

    return payments, orders, order_statuses, payment_statuses


def load_payment_statuses(connection, table):
    rows = connection.execute(
        select(
            table.c.payment_status_id,
            table.c.status_name,
        )
    ).mappings().all()

    statuses = {
        row["status_name"]: row["payment_status_id"]
        for row in rows
    }

    required = {
        "pending",
        "successful",
        "failed",
        "refunded",
    }

    missing = required - set(statuses)

    if missing:
        raise ValueError(
            f"Missing payment statuses: {missing}"
        )

    return statuses


def generate_provider_reference():
    return f"REW-{uuid.uuid4().hex[:20].upper()}"


def choose_payment_method():
    return random.choices(
        PAYMENT_METHODS,
        weights=PAYMENT_METHOD_WEIGHTS,
        k=1,
    )[0]


def random_payment_time(start_time, max_hours=48):
    return start_time + timedelta(
        minutes=random.randint(5, max_hours * 60)
    )


# PAYMENT RECORD GENERATION

def create_payment(
    order,
    payment_status_id,
    payment_status,
    created_at,
    paid_at=None,
):
    return {
        "order_id": order["order_id"],
        "payment_status_id": payment_status_id,
        "payment_method": choose_payment_method(),
        "amount": order["total_amount"],
        "currency": order["currency"],
        "provider_reference": generate_provider_reference(),
        "created_at": created_at,
        "paid_at": paid_at,
    }


def generate_payment_records(orders, payment_status_ids):
    records = []

    for order in orders:
        order_status = order["status_name"]
        order_created_at = order["created_at"]

        successful_payment_required = order_status in {
            "paid",
            "shipped",
            "delivered",
            "completed",
            "refunded",
        }

        if successful_payment_required:
            # Some orders have a failed attempt before succeeding
            if random.random() < EXTRA_ATTEMPT_PROBABILITY:
                failed_created_at = random_payment_time(
                    order_created_at,
                    max_hours=12,
                )

                records.append(
                    create_payment(
                        order,
                        payment_status_ids["failed"],
                        "failed",
                        failed_created_at,
                    )
                )

            payment_created_at = random_payment_time(
                order_created_at,
                max_hours=24,
            )

            payment_paid_at = payment_created_at + timedelta(
                minutes=random.randint(1, 30)
            )

            if order_status == "refunded":
                # A refunded order has a successful payment followed by a refund record
                records.append(
                    create_payment(
                        order,
                        payment_status_ids["successful"],
                        "successful",
                        payment_created_at,
                        payment_paid_at,
                    )
                )

                refund_created_at = payment_paid_at + timedelta(
                    days=random.randint(1, 10)
                )

                records.append(
                    create_payment(
                        order,
                        payment_status_ids["refunded"],
                        "refunded",
                        refund_created_at,
                        refund_created_at,
                    )
                )

            else:
                records.append(
                    create_payment(
                        order,
                        payment_status_ids["successful"],
                        "successful",
                        payment_created_at,
                        payment_paid_at,
                    )
                )

        elif order_status == "cancelled":
            # A cancelled order may have had a failed payment attempt
            if random.random() < 0.50:
                records.append(
                    create_payment(
                        order,
                        payment_status_ids["failed"],
                        "failed",
                        random_payment_time(
                            order_created_at,
                            max_hours=12,
                        ),
                    )
                )

            else:
                records.append(
                    create_payment(
                        order,
                        payment_status_ids["pending"],
                        "pending",
                        order_created_at,
                    )
                )

        else:
            # Pending and awaiting-payment orders
            if random.random() < UNPAID_FAILURE_PROBABILITY:
                records.append(
                    create_payment(
                        order,
                        payment_status_ids["failed"],
                        "failed",
                        random_payment_time(
                            order_created_at,
                            max_hours=12,
                        ),
                    )
                )

            else:
                records.append(
                    create_payment(
                        order,
                        payment_status_ids["pending"],
                        "pending",
                        order_created_at,
                    )
                )

    return records


def generate_payments():
    random.seed(RANDOM_SEED)

    print("Starting payment generation...")

    with engine.begin() as connection:
        (
            payments_table,
            orders_table,
            order_statuses_table,
            payment_statuses_table,
        ) = load_tables(connection)

        existing_payments = connection.execute(
            select(payments_table.c.payment_id)
        ).first()

        if existing_payments:
            raise ValueError(
                "The payments table already contains records. "
                "Generation stopped to prevent duplicates."
            )

        payment_status_ids = load_payment_statuses(
            connection,
            payment_statuses_table,
        )

        orders = connection.execute(
            select(
                orders_table.c.order_id,
                orders_table.c.order_status_id,
                orders_table.c.total_amount,
                orders_table.c.currency,
                orders_table.c.created_at,
                order_statuses_table.c.status_name,
            )
            .join(
                order_statuses_table,
                orders_table.c.order_status_id
                == order_statuses_table.c.order_status_id,
            )
            .order_by(orders_table.c.order_id)
        ).mappings().all()

        orders = [dict(order) for order in orders]

        print(f"Available orders: {len(orders):,}")

        if not orders:
            raise ValueError(
                "No orders found. Generate orders first."
            )

        payment_records = generate_payment_records(
            orders,
            payment_status_ids,
        )

        print(
            f"Generated payment attempts: "
            f"{len(payment_records):,}"
        )

        for start in range(
            0,
            len(payment_records),
            BATCH_SIZE,
        ):
            batch = payment_records[
                start:start + BATCH_SIZE
            ]

            connection.execute(
                insert(payments_table),
                batch,
            )

            inserted = min(
                start + BATCH_SIZE,
                len(payment_records),
            )

            print(
                f"Inserted {inserted:,} / "
                f"{len(payment_records):,} payments"
            )

    print("Payment generation completed successfully.")


if __name__ == "__main__":
    generate_payments()
