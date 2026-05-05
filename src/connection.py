import os

import snowflake.connector


def get_connection() -> snowflake.connector.SnowflakeConnection:
    """Return a Snowflake connection using environment variables.

    Required env vars: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD.
    Optional env vars: SNOWFLAKE_WAREHOUSE, SNOWFLAKE_ROLE, SNOWFLAKE_AUTHENTICATOR.

    Raises:
        EnvironmentError: If any required env var is missing or empty.
    """
    required = {
        "SNOWFLAKE_ACCOUNT": os.environ.get("SNOWFLAKE_ACCOUNT"),
        "SNOWFLAKE_USER": os.environ.get("SNOWFLAKE_USER"),
        "SNOWFLAKE_PASSWORD": os.environ.get("SNOWFLAKE_PASSWORD"),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    params = {
        "account": required["SNOWFLAKE_ACCOUNT"],
        "user": required["SNOWFLAKE_USER"],
        "password": required["SNOWFLAKE_PASSWORD"],
    }
    if wh := os.environ.get("SNOWFLAKE_WAREHOUSE"):
        params["warehouse"] = wh
    if role := os.environ.get("SNOWFLAKE_ROLE"):
        params["role"] = role
    if auth := os.environ.get("SNOWFLAKE_AUTHENTICATOR"):
        params["authenticator"] = auth

    return snowflake.connector.connect(**params)
