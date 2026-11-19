
from analytics.database import read_sql


def get_customer_summary():
    return read_sql("""
        SELECT *
        FROM vw_customer_purchase_summary
        ORDER BY total_spend DESC;
    """)


def get_customer_segments():
    return read_sql("""
        SELECT *
        FROM vw_customer_segments;
    """)


def get_repeat_purchase_metrics():
    return read_sql("""
        SELECT *
        FROM vw_repeat_purchase_metrics;
    """)


def get_cohort_retention():
    return read_sql("""
        SELECT *
        FROM vw_cohort_retention
        ORDER BY cohort_month, cohort_index;
    """)


def get_monthly_customer_acquisition():
    return read_sql("""
        SELECT *
        FROM vw_monthly_customer_acquisition
        ORDER BY month;
    """)


def get_customer_lifetime_value():
    return read_sql("""
        SELECT *
        FROM vw_customer_lifetime_value
        ORDER BY total_spend DESC;
    """)
