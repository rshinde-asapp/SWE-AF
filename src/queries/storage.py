def total_storage_daily() -> str:
    """Daily total storage bytes (no date params — view is historical)."""
    return """
        SELECT
            USAGE_DATE,
            AVERAGE_STAGE_BYTES,
            AVERAGE_DATABASE_BYTES,
            AVERAGE_FAILSAFE_BYTES,
            AVERAGE_STAGE_BYTES + AVERAGE_DATABASE_BYTES + AVERAGE_FAILSAFE_BYTES
                AS TOTAL_BYTES
        FROM SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE
        WHERE USAGE_DATE >= %s AND USAGE_DATE < %s
        ORDER BY USAGE_DATE
    """


def storage_by_database(start_date: str = "%s", end_date: str = "%s") -> str:
    """Latest storage per database. Params: (start_date, end_date)."""
    return """
        SELECT
            DATABASE_NAME,
            AVG(AVERAGE_DATABASE_BYTES) AS AVG_DATABASE_BYTES,
            AVG(AVERAGE_FAILSAFE_BYTES) AS AVG_FAILSAFE_BYTES
        FROM SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY
        WHERE USAGE_DATE >= %s AND USAGE_DATE < %s
        GROUP BY 1
        ORDER BY 2 DESC
    """
