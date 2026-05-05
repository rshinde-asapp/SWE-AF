from src.queries.warehouse import (
    daily_total_credits,
    warehouse_credits_daily,
    warehouse_total_credits,
)

TABLE = "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY"


def test_warehouse_credits_daily():
    sql = warehouse_credits_daily()
    assert TABLE in sql
    assert sql.count("%s") >= 2
    assert "SELECT" in sql
    assert "FROM" in sql
    assert "WHERE" in sql


def test_warehouse_total_credits():
    sql = warehouse_total_credits()
    assert TABLE in sql
    assert sql.count("%s") >= 2
    assert "SELECT" in sql
    assert "FROM" in sql
    assert "WHERE" in sql


def test_daily_total_credits():
    sql = daily_total_credits()
    assert TABLE in sql
    assert sql.count("%s") >= 2
    assert "SELECT" in sql
    assert "FROM" in sql
    assert "WHERE" in sql
