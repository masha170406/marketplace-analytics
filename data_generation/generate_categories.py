
from sqlalchemy import text

from database.connection import engine


CATEGORIES = [
    # Root categories
    ("Women", None),
    ("Men", None),
    ("Kids", None),
    ("Home", None),
    ("Electronics", None),

    # Women
    ("Clothing", "Women"),
    ("Shoes", "Women"),
    ("Bags", "Women"),
    ("Accessories", "Women"),

    # Men
    ("Clothing", "Men"),
    ("Shoes", "Men"),
    ("Accessories", "Men"),

    # Kids
    ("Clothing", "Kids"),
    ("Shoes", "Kids"),
    ("Toys", "Kids"),

    # Home
    ("Home Decor", "Home"),
    ("Kitchen", "Home"),
    ("Textiles", "Home"),

    # Electronics
    ("Phones", "Electronics"),
    ("Computers", "Electronics"),

    # Women's clothing subcategories
    ("Dresses", "Women/Clothing"),
    ("Tops", "Women/Clothing"),
    ("Jeans", "Women/Clothing"),
    ("Trousers", "Women/Clothing"),
    ("Coats & Jackets", "Women/Clothing"),
    ("Sweaters", "Women/Clothing"),
    ("Sportswear", "Women/Clothing"),

    # Women's shoes subcategories
    ("Sneakers", "Women/Shoes"),
    ("Boots", "Women/Shoes"),
    ("Sandals", "Women/Shoes"),

    # Women's bags subcategories
    ("Handbags", "Women/Bags"),
    ("Backpacks", "Women/Bags"),

    # Women's accessories subcategories
    ("Jewellery", "Women/Accessories"),
    ("Watches", "Women/Accessories"),
    ("Sunglasses", "Women/Accessories"),
]


def generate_categories():

    print("Starting category generation...")

    with engine.begin() as connection:

        # Check whether categories already exist
        existing_count = connection.execute(
            text("SELECT COUNT(*) FROM categories")
        ).scalar_one()

        if existing_count > 0:
            print(
                f"Found {existing_count} existing categories. "
                "Skipping generation."
            )
            return

        # Dictionary mapping category paths to database IDs
        category_ids = {}

        # Insert root categories

        for category_name, parent_path in CATEGORIES:

            if parent_path is None:

                result = connection.execute(
                    text("""
                        INSERT INTO categories (
                            category_name,
                            parent_category_id
                        )
                        VALUES (:category_name, NULL)
                        RETURNING category_id
                    """),
                    {
                        "category_name": category_name
                    }
                )

                category_id = result.scalar_one()

                category_ids[category_name] = category_id

                print(f"Inserted root category: {category_name}")

        # Insert child categories

        remaining_categories = [
            (name, parent)
            for name, parent in CATEGORIES
            if parent is not None
        ]

        # Insert only after the parent exists
        while remaining_categories:

            inserted_this_round = []

            for category_name, parent_path in remaining_categories:

                if parent_path not in category_ids:
                    continue

                parent_id = category_ids[parent_path]

                result = connection.execute(
                    text("""
                        INSERT INTO categories (
                            category_name,
                            parent_category_id
                        )
                        VALUES (
                            :category_name,
                            :parent_id
                        )
                        RETURNING category_id
                    """),
                    {
                        "category_name": category_name,
                        "parent_id": parent_id
                    }
                )

                category_id = result.scalar_one()

                # Store the complete path as the dictionary key
                category_path = f"{parent_path}/{category_name}"

                category_ids[category_path] = category_id

                inserted_this_round.append(
                    (category_name, parent_path)
                )

                print(f"Inserted category: {category_path}")

            if not inserted_this_round:
                raise ValueError(
                    "Unable to insert remaining categories. "
                    "Check for missing or incorrectly defined parents."
                )

            remaining_categories = [
                category
                for category in remaining_categories
                if category not in inserted_this_round
            ]

    print("\nCategory generation completed successfully.")
    print(f"Total categories inserted: {len(category_ids)}")


if __name__ == "__main__":
    generate_categories()
