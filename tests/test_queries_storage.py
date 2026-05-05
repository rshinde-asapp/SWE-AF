from src.queries.storage import total_storage_daily, storage_by_database


def test_storage_total_storage_daily_references_view():
    sql = total_storage_daily()
    assert "SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE" in sql


def test_storage_total_storage_daily_has_placeholders():
    sql = total_storage_daily()
    assert "%s" in sql


def test_storage_total_storage_daily_structure():
    sql = total_storage_daily()
    assert "SELECT" in sql
    assert "FROM" in sql
    assert "WHERE" in sql


def test_storage_by_database_references_view():
    sql = storage_by_database()
    assert "SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY" in sql


def test_storage_by_database_has_placeholders():
    sql = storage_by_database()
    assert "%s" in sql
