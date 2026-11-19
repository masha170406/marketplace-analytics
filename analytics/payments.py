
from analytics.database import read_sql


def get_payment_performance():
    return read_sql("""
        SELECT *
        FROM vw_payment_performance;
    """)


def get_payment_method_performance():
    return read_sql("""
        SELECT *
        FROM vw_payment_method_performance
        ORDER BY total_attempts DESC;
    """)


def get_monthly_payment_trends():
    return read_sql("""
        SELECT *
        FROM vw_monthly_payment_trends
        ORDER BY month;
    """)


def get_payment_attempt_distribution():
    return read_sql("""
        SELECT *
        FROM vw_payment_attempt_distribution
        ORDER BY attempts_per_order;
    """)


def get_refund_analysis():
    return read_sql("""
        SELECT *
        FROM vw_refund_analysis;
    """)


def get_order_payment_reconciliation():
    return read_sql("""
        SELECT *
        FROM vw_order_payment_reconciliation;
    """)
