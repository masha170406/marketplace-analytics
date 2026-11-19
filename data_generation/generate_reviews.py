
import random
from datetime import timedelta

from sqlalchemy import (
    MetaData,
    Table,
    select,
    insert,
)

from database.connection import engine

RANDOM_SEED = 42
BATCH_SIZE = 1000

REVIEW_PROBABILITY = 0.70

RATING_VALUES = [1, 2, 3, 4, 5]
RATING_WEIGHTS = [0.02, 0.04, 0.12, 0.37, 0.45]



REVIEW_COMMENTS = {
    1: [
        "Very disappointing experience.",
        "The item was not as described.",
        "Unfortunately, I had problems with this purchase.",
        "Not happy with the condition of the item.",
        "The transaction did not meet my expectations.",
    ],
    2: [
        "The experience could have been better.",
        "The item had some issues.",
        "Delivery took longer than expected.",
        "Communication could have been improved.",
        "Not entirely satisfied with this purchase.",
    ],
    3: [
        "Overall, an average experience.",
        "The item was okay for the price.",
        "Everything was acceptable.",
        "The purchase went as expected.",
        "A decent transaction overall.",
    ],
    4: [
        "Good experience, would buy again.",
        "Item arrived in good condition.",
        "Great communication and smooth transaction.",
        "Happy with my purchase.",
        "Everything went smoothly.",
        "Good seller, recommended.",
    ],
    5: [
        "Excellent experience!",
        "Perfect item and very friendly seller.",
        "Exactly as described. Highly recommended!",
        "Fast shipping and great communication.",
        "Amazing seller, would definitely buy again!",
        "Very happy with this purchase!",
        "Everything was perfect. Thank you!",
    ],
}


def load_tables(connection):
    metadata = MetaData()

    reviews = Table(
        "reviews",
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

    return reviews, orders, order_statuses


def choose_rating():
    return random.choices(
        RATING_VALUES,
        weights=RATING_WEIGHTS,
        k=1,
    )[0]


def generate_comment(rating):
    return random.choice(REVIEW_COMMENTS[rating])


def generate_review_date(completed_at):
    """
    Generate a review date between 1 and 21 days
    after order completion.
    """
    return completed_at + timedelta(
        days=random.randint(1, 21),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )

# GENERATE REVIEW RECORDS

def generate_review_records(completed_orders):
    review_records = []

    for order in completed_orders:
        if random.random() > REVIEW_PROBABILITY:
            continue

        rating = choose_rating()

        completed_at = order["completed_at"]

        if completed_at is None:
            continue

        review_records.append({
            "order_id": order["order_id"],
            "reviewer_id": order["buyer_id"],
            "reviewee_id": order["seller_id"],
            "rating": rating,
            "comment": generate_comment(rating),
            "created_at": generate_review_date(completed_at),
        })

    return review_records


def generate_reviews():
    random.seed(RANDOM_SEED)

    print("Starting review generation...")

    with engine.begin() as connection:
        (
            reviews_table,
            orders_table,
            order_statuses_table,
        ) = load_tables(connection)

        # Prevent duplicate generation
        existing_reviews = connection.execute(
            select(reviews_table.c.review_id).limit(1)
        ).first()

        if existing_reviews:
            raise ValueError(
                "The reviews table already contains records. "
                "Generation stopped to prevent duplicates."
            )

        # Load completed orders only
        completed_orders = connection.execute(
            select(
                orders_table.c.order_id,
                orders_table.c.buyer_id,
                orders_table.c.seller_id,
                orders_table.c.completed_at,
            )
            .join(
                order_statuses_table,
                orders_table.c.order_status_id
                == order_statuses_table.c.order_status_id,
            )
            .where(
                order_statuses_table.c.status_name == "completed",
                orders_table.c.completed_at.is_not(None),
            )
        ).mappings().all()

        completed_orders = [
            dict(order)
            for order in completed_orders
        ]

        print(
            f"Completed orders available: "
            f"{len(completed_orders):,}"
        )

        if not completed_orders:
            raise ValueError(
                "No completed orders found. "
                "Generate orders first."
            )

        review_records = generate_review_records(
            completed_orders
        )

        print(
            f"Generated reviews: {len(review_records):,}"
        )

        # Insert in batches.
        for start in range(
            0,
            len(review_records),
            BATCH_SIZE,
        ):
            batch = review_records[
                start:start + BATCH_SIZE
            ]

            connection.execute(
                insert(reviews_table),
                batch,
            )

            inserted = min(
                start + BATCH_SIZE,
                len(review_records),
            )

            print(
                f"Inserted {inserted:,} / "
                f"{len(review_records):,} reviews"
            )

    print("Review generation completed successfully.")


if __name__ == "__main__":
    generate_reviews()
