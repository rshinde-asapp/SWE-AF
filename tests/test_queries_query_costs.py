from src.queries.query_costs import (
    credits_by_query_type,
    credits_by_user,
    top_queries_by_cost,
)


def test_query_costs_top_queries_by_cost_structure():
    sql = top_queries_by_cost()
    assert "SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY" in sql
    assert "%s" in sql
    assert "SELECT" in sql
    assert "FROM" in sql
    assert "WHERE" in sql
    assert "LIMIT 50" in sql
    assert "LEFT(QUERY_TEXT, 200)" in sql


def test_query_costs_credits_by_query_type_structure():
    sql = credits_by_query_type()
    assert "SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY" in sql
    assert "%s" in sql
    assert "SELECT" in sql
    assert "FROM" in sql
    assert "WHERE" in sql


def test_query_costs_credits_by_user_structure():
    sql = credits_by_user()
    assert "SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY" in sql
    assert "%s" in sql
    assert "SELECT" in sql
    assert "FROM" in sql
    assert "WHERE" in sql
