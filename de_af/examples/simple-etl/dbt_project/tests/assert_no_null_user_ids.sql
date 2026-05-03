-- Custom data quality test: Assert no NULL user_ids in staging table
-- This test fails if any rows are returned

SELECT
    user_id,
    email,
    created_at
FROM {{ ref('stg_users') }}
WHERE user_id IS NULL
