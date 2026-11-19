
import pandas as pd
from sqlalchemy import text

from database.connection import engine


def read_sql(query: str) -> pd.DataFrame:
    """
    Execute a SQL query and return the results as a DataFrame.
    """
    try:
        with engine.connect() as connection:
            return pd.read_sql(
                text(query),
                connection
            )

    except Exception as error:
        print(f"Database query failed: {error}")
        raise
