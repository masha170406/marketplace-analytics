
from analytics.database import read_sql


def get_monthly_sales():
    return read_sql("""
        SELECT *
        FROM vw_monthly_sales
        ORDER BY month;
    """)


def get_category_performance():
    return read_sql("""
        SELECT *
        FROM vw_category_performance
        ORDER BY gmv DESC;
    """)


def get_monthly_category_sales():
    return read_sql("""
        SELECT *
        FROM vw_monthly_category_sales
        ORDER BY month;
    """)


def get_order_value_distribution():
    return read_sql("""
        SELECT *
        FROM vw_order_value_distribution;
    """)


def get_order_status_distribution():
    return read_sql("""
        SELECT *
        FROM vw_order_status_distribution
        ORDER BY order_count DESC;
    """)


def get_top_selling_categories():
    return read_sql("""
        SELECT *
        FROM vw_top_selling_categories
        ORDER BY gmv DESC
        LIMIT 10;
    """)
