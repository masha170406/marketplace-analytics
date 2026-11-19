
import random
from datetime import datetime, timedelta

import numpy as np
from faker import Faker
from sqlalchemy import MetaData, Table, insert, text

from database.connection import engine


fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

NUMBER_OF_LISTINGS = 15_000
BATCH_SIZE = 1_000

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31, 23, 59, 59)

CONDITIONS = [
    "new_with_tags",
    "new_without_tags",
    "very_good",
    "good",
    "satisfactory",
]

CONDITION_PROBABILITIES = [
    0.10, 0.15, 0.35, 0.30, 0.10
]

STATUS_PROBABILITIES = {
    "draft": 0.05,
    "active": 0.35,
    "reserved": 0.05,
    "sold": 0.38,
    "expired": 0.10,
    "removed": 0.07,
}

BASE_PRICES = {
    "Dresses": 35,
    "Tops": 18,
    "Jeans": 30,
    "Trousers": 28,
    "Coats & Jackets": 65,
    "Sweaters": 30,
    "Sportswear": 25,
    "Sneakers": 45,
    "Boots": 55,
    "Sandals": 25,
    "Handbags": 40,
    "Backpacks": 30,
    "Jewellery": 20,
    "Watches": 50,
    "Sunglasses": 25,
    "Phones": 180,
    "Computers": 350,
    "Toys": 20,
    "Home Decor": 25,
    "Kitchen": 20,
    "Textiles": 25,
}

CONDITION_MULTIPLIERS = {
    "new_with_tags": 1.00,
    "new_without_tags": 0.90,
    "very_good": 0.75,
    "good": 0.60,
    "satisfactory": 0.40,
}


# PRICE GENERATION

def generate_price(category_name, condition):

    base_price = BASE_PRICES.get(category_name, 30)

    price = (
        base_price
        * CONDITION_MULTIPLIERS[condition]
        * np.random.lognormal(mean=0, sigma=0.30)
    )

    return round(float(np.clip(price, 5, 500)), 2)


# TITLE AND DESCRIPTION GENERATION

def generate_title(category_name):

    brand = random.choice([
        "Zara",
        "Nike",
        "Adidas",
        "H&M",
        "Mango",
        "Levi's",
        "Reserved",
        "COS",
        "Uniqlo",
        "Vintage",
        "Other",
    ])

    adjective = random.choice([
        "Classic",
        "Stylish",
        "Casual",
        "Vintage",
        "Elegant",
        "Comfortable",
        "Minimalist",
        "Premium",
        "Everyday",
    ])

    return f"{brand} {adjective} {category_name}"


def generate_description(title, condition):

    descriptions = [
        f"{title}. A great addition to your wardrobe.",
        f"{title}. Well maintained and ready for a new owner.",
        f"{title}. Selling because I no longer need it.",
        f"{title}. Carefully stored and in "
        f"{condition.replace('_', ' ')} condition.",
        f"{title}. Perfect for everyday use.",
    ]

    return random.choice(descriptions)


# LOAD REFERENCE DATA FROM POSTGRESQL

def load_reference_data(connection):

    sellers = connection.execute(
        text("""
            SELECT user_id
            FROM users
            WHERE account_status = 'active'
        """)
    ).scalars().all()

    categories = connection.execute(
        text("""
            SELECT
                c.category_id,
                c.category_name
            FROM categories c
            WHERE NOT EXISTS (
                SELECT 1
                FROM categories child
                WHERE child.parent_category_id = c.category_id
            )
        """)
    ).mappings().all()

    statuses = connection.execute(
        text("""
            SELECT
                listing_status_id,
                status_name
            FROM listing_statuses
        """)
    ).mappings().all()

    if not sellers:
        raise ValueError(
            "No active users found. Generate users first."
        )

    if not categories:
        raise ValueError(
            "No leaf categories found. Check categories table."
        )

    status_ids = {
        row["status_name"]: row["listing_status_id"]
        for row in statuses
    }

    missing_statuses = (
        set(STATUS_PROBABILITIES.keys()) - set(status_ids.keys())
    )

    if missing_statuses:
        raise ValueError(
            f"Missing listing statuses: {missing_statuses}"
        )

    return sellers, categories, status_ids

# GENERATE LISTING RECORDS

def generate_listing_records(sellers, categories):

    records = []

    category_choices = np.random.choice(
        len(categories),
        size=NUMBER_OF_LISTINGS
    )

    seller_choices = np.random.choice(
        sellers,
        size=NUMBER_OF_LISTINGS
    )

    status_names = list(STATUS_PROBABILITIES.keys())
    status_weights = list(STATUS_PROBABILITIES.values())

    selected_statuses = np.random.choice(
        status_names,
        size=NUMBER_OF_LISTINGS,
        p=status_weights
    )

    for i in range(NUMBER_OF_LISTINGS):

        category = categories[category_choices[i]]

        category_id = int(category["category_id"])
        category_name = category["category_name"]

        seller_id = int(seller_choices[i])
        status_name = selected_statuses[i]

        condition = np.random.choice(
            CONDITIONS,
            p=CONDITION_PROBABILITIES
        )

        created_at = fake.date_time_between(
            start_date=START_DATE,
            end_date=END_DATE
        )

        if status_name == "draft":
            published_at = None
        else:
            published_at = created_at + timedelta(
                hours=random.randint(1, 48)
            )

        expires_at = created_at + timedelta(days=90)

        title = generate_title(category_name)

        records.append({
            "seller_id": seller_id,
            "category_id": category_id,
            "title": title,
            "description": generate_description(
                title,
                condition
            ),
            "condition": condition,
            "price": generate_price(
                category_name,
                condition
            ),
            "currency": "EUR",
            "listing_status_id": None,
            "created_at": created_at,
            "published_at": published_at,
            "expires_at": expires_at,
            "_status_name": status_name,
        })

    return records

# GENERATE LISTING STATUS HISTORY

def generate_listing_history(
    listing_ids,
    records,
    status_ids
):

    history_records = []

    for listing_id, listing in zip(listing_ids, records):

        created_at = listing["created_at"]
        published_at = listing["published_at"]
        seller_id = listing["seller_id"]
        final_status = listing["_status_name"]

        # Every listing starts as a draft
        history_records.append({
            "listing_id": listing_id,
            "listing_status_id": status_ids["draft"],
            "changed_by_user_id": seller_id,
            "changed_at": created_at,
            "change_reason": "Listing created",
        })

        # Record the next status transition
        if final_status != "draft":

            history_date = published_at

            if final_status in ("sold", "expired", "removed"):
                history_date += timedelta(
                    days=random.randint(1, 89)
                )

            elif final_status == "reserved":
                history_date += timedelta(
                    days=random.randint(0, 10)
                )

            history_records.append({
                "listing_id": listing_id,
                "listing_status_id": status_ids[final_status],
                "changed_by_user_id": seller_id,
                "changed_at": history_date,
                "change_reason": (
                    f"Listing status changed to {final_status}"
                ),
            })

    return history_records


# INSERT LISTINGS AND HISTORY INTO POSTGRESQL

def generate_listings():

    print("Starting listing generation...")

    metadata = MetaData()

    listings_table = Table(
        "listings",
        metadata,
        autoload_with=engine
    )

    history_table = Table(
        "listing_status_history",
        metadata,
        autoload_with=engine
    )

    with engine.begin() as connection:

        existing = connection.execute(
            text("SELECT COUNT(*) FROM listings")
        ).scalar()

        if existing > 0:
            print(
                f"Listings table already contains {existing} records."
            )
            print("Skipping listing generation.")
            return

        sellers, categories, status_ids = load_reference_data(
            connection
        )

        print(f"Available sellers: {len(sellers)}")
        print(f"Available leaf categories: {len(categories)}")

        records = generate_listing_records(
            sellers,
            categories
        )

        # Assign actual database status IDs
        for record in records:
            record["listing_status_id"] = status_ids[
                record["_status_name"]
            ]

        listing_ids = []

        print("Inserting listings...")

        for start in range(0, len(records), BATCH_SIZE):

            batch = records[start:start + BATCH_SIZE]

            clean_batch = [
                {
                    key: value
                    for key, value in record.items()
                    if not key.startswith("_")
                }
                for record in batch
            ]

            result = connection.execute(
                insert(listings_table).returning(
                    listings_table.c.listing_id
                ),
                clean_batch
            )

            listing_ids.extend(result.scalars().all())

            print(
                f"Inserted {len(listing_ids)}/{NUMBER_OF_LISTINGS} "
                "listings"
            )

        print("Generating listing status histories...")

        history_records = generate_listing_history(
            listing_ids,
            records,
            status_ids
        )

        for start in range(0, len(history_records), BATCH_SIZE):

            batch = history_records[start:start + BATCH_SIZE]

            connection.execute(
                insert(history_table),
                batch
            )

        print(
            f"Inserted {len(history_records)} history records."
        )

    print("Listing generation completed successfully.")



if __name__ == "__main__":
    generate_listings()
