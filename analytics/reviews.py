
from analytics.database import read_sql


def get_review_metrics():
    return read_sql("""
        SELECT *
        FROM vw_review_metrics;
    """)


def get_review_rating_distribution():
    return read_sql("""
        SELECT *
        FROM vw_review_rating_distribution
        ORDER BY rating;
    """)


def get_seller_reputation():
    return read_sql("""
        SELECT *
        FROM vw_seller_reputation
        ORDER BY average_rating DESC;
    """)


def get_top_rated_sellers():
    return read_sql("""
        SELECT *
        FROM vw_top_rated_sellers
        ORDER BY rating_rank
        LIMIT 20;
    """)


def get_monthly_review_trends():
    return read_sql("""
        SELECT *
        FROM vw_monthly_review_trends
        ORDER BY month;
    """)


def get_review_country_performance():
    return read_sql("""
        SELECT *
        FROM vw_review_country_performance
        ORDER BY average_rating DESC;
    """)


def get_review_response_summary():
    return read_sql("""
        SELECT *
        FROM vw_review_response_summary;
    """)
