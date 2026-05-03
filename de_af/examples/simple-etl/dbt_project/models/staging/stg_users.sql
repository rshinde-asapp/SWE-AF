-- Staging transformation: Clean raw CSV data
-- Remove duplicates, trim whitespace, cast types, filter invalid rows

WITH source_data AS (
    SELECT
        user_id,
        email,
        status,
        created_at
    FROM {{ source('raw', 'users_csv') }}
),

cleaned AS (
    SELECT
        CAST(user_id AS INTEGER) AS user_id,
        TRIM(LOWER(email)) AS email,
        TRIM(LOWER(status)) AS status,
        CAST(created_at AS DATE) AS created_at
    FROM source_data
    WHERE user_id IS NOT NULL
      AND email IS NOT NULL
      AND email LIKE '%@%'  -- Basic email validation
      AND status IN ('active', 'inactive', 'suspended')
),

deduplicated AS (
    SELECT
        user_id,
        email,
        status,
        created_at,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS row_num
    FROM cleaned
)

SELECT
    user_id,
    email,
    status,
    created_at
FROM deduplicated
WHERE row_num = 1
