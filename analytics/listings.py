
from analytics.database import read_sql


def get_listing_status_distribution():
    return read_sql("""
        SELECT *
        FROM vw_listing_status_distribution;
    """)


def get_listing_inventory():
    return read_sql("""
        SELECT *
        FROM vw_listing_inventory_summary;
    """)


def get_listing_category_performance():
    return read_sql("""
        SELECT *
        FROM vw_listing_category_performance
        ORDER BY total_listings DESC;
    """)


def get_monthly_listing_creation():
    return read_sql("""
        SELECT *
        FROM vw_monthly_listing_creation
        ORDER BY month;
    """)


def get_listing_time_to_sale():
    return read_sql("""
        SELECT *
        FROM vw_listing_time_to_sale;
    """)


def get_category_time_to_sale():
    return read_sql("""
        SELECT *
        FROM vw_category_time_to_sale
        ORDER BY average_days_to_sold;
    """)


def get_listing_price_distribution():
    return read_sql("""
        SELECT *
        FROM vw_listing_price_distribution;
    """)
