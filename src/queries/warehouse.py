def warehouse_credits_daily(start_date: str = "%s", end_date: str = "%s") -> str:
    """Daily credits per warehouse. Params: (start_date, end_date)."""
    return """
        SELECT
            WAREHOUSE_NAME,
            DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
            SUM(CREDITS_USED) AS TOTAL_CREDITS,
            SUM(CREDITS_USED_COMPUTE) AS COMPUTE_CREDITS,
            SUM(CREDITS_USED_CLOUD_SERVICES) AS CLOUD_CREDITS
        FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
        WHERE START_TIME >= %s AND START_TIME < %s
        GROUP BY 1, 2
        ORDER BY 2 DESC, 3 DESC
    """


def warehouse_total_credits(start_date: str = "%s", end_date: str = "%s") -> str:
    """Total credits per warehouse. Params: (start_date, end_date)."""
    return """
        SELECT
            WAREHOUSE_NAME,
            SUM(CREDITS_USED) AS TOTAL_CREDITS,
            SUM(CREDITS_USED_COMPUTE) AS COMPUTE_CREDITS,
            SUM(CREDITS_USED_CLOUD_SERVICES) AS CLOUD_CREDITS
        FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
        WHERE START_TIME >= %s AND START_TIME < %s
        GROUP BY 1
        ORDER BY 2 DESC
    """


def daily_total_credits(start_date: str = "%s", end_date: str = "%s") -> str:
    """Daily total credits across all warehouses. Params: (start_date, end_date)."""
    return """
        SELECT
            DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
            SUM(CREDITS_USED) AS TOTAL_CREDITS
        FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
        WHERE START_TIME >= %s AND START_TIME < %s
        GROUP BY 1
        ORDER BY 1
    """
