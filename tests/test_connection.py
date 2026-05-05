import pytest
from unittest.mock import patch, MagicMock

from src.connection import get_connection


def test_missing_required_vars_raises(env_missing_account):
    with pytest.raises(EnvironmentError) as exc_info:
        get_connection()
    error_msg = str(exc_info.value)
    assert "SNOWFLAKE_ACCOUNT" in error_msg
    assert "SNOWFLAKE_USER" in error_msg
    assert "SNOWFLAKE_PASSWORD" in error_msg


def test_missing_single_var_raises(monkeypatch):
    monkeypatch.setenv("SNOWFLAKE_USER", "test_user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "test_password")
    monkeypatch.delenv("SNOWFLAKE_ACCOUNT", raising=False)
    with pytest.raises(EnvironmentError) as exc_info:
        get_connection()
    assert "SNOWFLAKE_ACCOUNT" in str(exc_info.value)


def test_all_vars_set_calls_connect(env_with_creds):
    mock_conn = MagicMock()
    with patch("snowflake.connector.connect", return_value=mock_conn) as mock_connect:
        conn = get_connection()
        mock_connect.assert_called_once_with(
            account="test_account",
            user="test_user",
            password="test_password",
        )
        assert conn is mock_conn
