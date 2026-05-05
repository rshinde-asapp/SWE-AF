from src.queries.anomalies import warehouse_daily_with_zscore


def test_anomalies_daily_with_zscore():
    sql = warehouse_daily_with_zscore()
    assert "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY" in sql
    assert "%s" in sql
    assert "AVG(" in sql
    assert "STDDEV(" in sql
    assert "OVER" in sql
    assert "ROWS BETWEEN" in sql
    assert "13 PRECEDING AND CURRENT ROW" in sql
    assert "Z_SCORE" in sql
    assert "WAREHOUSE_NAME" in sql
    assert "USAGE_DATE" in sql
    assert "DAILY_CREDITS" in sql
    assert "ROLLING_AVG" in sql
    assert "ROLLING_STDDEV" in sql
    assert "STDDEV" in sql and "= 0 THEN 0" in sql
