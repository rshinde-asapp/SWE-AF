-- Dimension table: User dimension with SCD Type 1 (overwrite)
-- Business keys: user_id
-- Attributes: email, status, created_at, updated_at

WITH staging AS (
    SELECT
        user_id,
        email,
        status,
        created_at
    FROM {{ ref('stg_users') }}
),

enriched AS (
    SELECT
        user_id,
        email,
        status,
        created_at,
        CURRENT_TIMESTAMP() AS updated_at,
        CASE
            WHEN status = 'active' THEN TRUE
            ELSE FALSE
        END AS is_active,
        DATEDIFF(day, created_at, CURRENT_DATE()) AS days_since_creation
    FROM staging
)

SELECT
    user_id,
    email,
    status,
    is_active,
    created_at,
    days_since_creation,
    updated_at
FROM enriched
