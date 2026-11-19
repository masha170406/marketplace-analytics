
import numpy as np
import pandas as pd

from faker import Faker
from sqlalchemy import text

from database.connection import engine


fake = Faker()
Faker.seed(42)
np.random.seed(42)

NUMBER_OF_USERS = 10_000

COUNTRIES = [
    "Lithuania",
    "Poland",
    "Germany",
    "France",
    "Spain",
    "Italy",
    "Netherlands",
    "Belgium",
    "Czech Republic",
    "Sweden"
]

COUNTRY_PROBABILITIES = [
    0.08, 0.15, 0.18, 0.14, 0.10,
    0.10, 0.08, 0.05, 0.07, 0.05
]


def generate_users():

    print("Generating users...")

    registration_dates = pd.to_datetime(
        np.random.choice(
            pd.date_range("2024-01-01", "2025-12-31"),
            size=NUMBER_OF_USERS
        )
    )

    users = []

    for i in range(NUMBER_OF_USERS):

        users.append({
            "username": f"{fake.user_name()}_{i}",
            "email": f"rewear_user_{i}@example.com",
            "country": np.random.choice(
                COUNTRIES,
                p=COUNTRY_PROBABILITIES
            ),
            "registration_date": registration_dates[i].to_pydatetime(),
            "account_status": np.random.choice(
                ["active", "suspended", "deleted"],
                p=[0.96, 0.03, 0.01]
            )
        })

    df = pd.DataFrame(users)

    print(f"Generated {len(df)} users.")

    # Insert in batches
    records = df.to_dict(orient="records")

    with engine.begin() as connection:

        existing = connection.execute(
            text("SELECT COUNT(*) FROM users")
        ).scalar()

        if existing > 0:
            print("Users already exist. Skipping generation.")
            return

        batch_size = 1000

        insert_query = text("""
            INSERT INTO users (
                username,
                email,
                country,
                registration_date,
                account_status
            )
            VALUES (
                :username,
                :email,
                :country,
                :registration_date,
                :account_status
            )
        """)

        for start in range(0, len(records), batch_size):

            batch = records[start:start + batch_size]

            connection.execute(insert_query, batch)

            print(
                f"Inserted {min(start + batch_size, len(records))}"
                f"/{NUMBER_OF_USERS} users"
            )

    print("Users generated successfully.")


if __name__ == "__main__":
    generate_users()
