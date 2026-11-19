
from analytics.database import read_sql


def get_marketplace_kpis():
    query = """
        SELECT *
        FROM vw_marketplace_kpis;
    """
    return read_sql(query)


def get_monthly_marketplace_metrics():
    query = """
        SELECT *
        FROM vw_monthly_marketplace_metrics
        ORDER BY month;
    """
    return read_sql(query)
