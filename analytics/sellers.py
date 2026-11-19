
from analytics.database import read_sql


def get_seller_performance():
    return read_sql("""
        SELECT *
        FROM vw_seller_performance
        ORDER BY total_gmv DESC;
    """)


def get_top_sellers():
    return read_sql("""
        SELECT *
        FROM vw_top_sellers
        ORDER BY gmv_rank
        LIMIT 20;
    """)


def get_seller_country_performance():
    return read_sql("""
        SELECT *
        FROM vw_seller_country_performance
        ORDER BY total_gmv DESC;
    """)


def get_monthly_seller_performance():
    return read_sql("""
        SELECT *
        FROM vw_monthly_seller_performance
        ORDER BY month;
    """)


def get_seller_rating_distribution():
    return read_sql("""
        SELECT *
        FROM vw_seller_rating_distribution
        ORDER BY rating;
    """)


def get_seller_segments():
    return read_sql("""
        SELECT *
        FROM vw_seller_segments;
    """)
