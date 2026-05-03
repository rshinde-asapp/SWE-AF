# Mock Snowflake warehouse for simple ETL example

resource "snowflake_warehouse" "etl_warehouse" {
  name           = "SIMPLE_ETL_WH"
  warehouse_size = "XSMALL"
  auto_suspend   = 300  # 5 minutes
  auto_resume    = true
  comment        = "Warehouse for simple CSV to Parquet ETL pipeline"
}

resource "snowflake_database" "analytics" {
  name    = "ANALYTICS"
  comment = "Analytics database for simple ETL example"
}

resource "snowflake_schema" "staging" {
  database = snowflake_database.analytics.name
  name     = "STAGING"
  comment  = "Staging schema for raw data transformations"
}

resource "snowflake_schema" "marts" {
  database = snowflake_database.analytics.name
  name     = "MARTS"
  comment  = "Data marts schema for analytics-ready tables"
}
