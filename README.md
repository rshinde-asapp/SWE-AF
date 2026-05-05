# Snowflake Cost Intelligence Dashboard

A local Streamlit multi-page application that reads Snowflake credentials from environment variables, queries `SNOWFLAKE.ACCOUNT_USAGE` views, and renders interactive Plotly dashboard pages.

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**

   ```bash
   export SNOWFLAKE_ACCOUNT=<your_account>
   export SNOWFLAKE_USER=<your_user>
   export SNOWFLAKE_PASSWORD=<your_password>
   # Optional:
   export SNOWFLAKE_WAREHOUSE=<warehouse>
   export SNOWFLAKE_ROLE=<role>
   ```

## Run

```bash
streamlit run app.py
```

## Run Tests

```bash
pytest tests/
```
