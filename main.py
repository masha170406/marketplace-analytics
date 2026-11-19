
from data_generation.generate_reviews import generate_reviews
from data_generation.generate_users import generate_users
from data_generation.generate_categories import generate_categories
from data_generation.generate_listings import generate_listings
from data_generation.generate_orders import generate_orders
from data_generation.generate_payments import generate_payments


def main():
    print("Starting ReWear data generation...")

    #generate_categories()
    #generate_users()
    #generate_listings()
    #generate_orders()
    #generate_payments()
    generate_reviews()

    print("All data generation completed!")


if __name__ == "__main__":
    main()
