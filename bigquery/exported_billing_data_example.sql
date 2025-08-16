-- ------------------------------------------------------------
-- USE CASE (BigQuery-focused):
-- This query helps you understand spend on BigQuery specifically by reading
-- your Google Cloud billing export in BigQuery and subtotaling the different
-- BigQuery cost components (for example: query/analysis, storage, streaming inserts,
-- load jobs, copy jobs, and other SKU-level charges).
--
-- WHAT IT RETURNS:
-- It returns a subtotaled list of BigQuery cost components and their total USD
-- cost over the selected time window (the query groups SKUs into human-friendly
-- activity buckets and sums the cost for each bucket).
--
-- HOW IT WORKS:
-- The query reads rows from your billing export table filtered to service = 'BigQuery',
-- extracts the SKU description, maps SKUs into activity groups (analysis/query, storage,
-- streaming, load, copy, etc.), and then aggregates costs per activity.
--
-- REQUIREMENTS TO USE:
-- - Billing export must be enabled in Google Cloud.
-- - You must use the resource-level billing export (resource-level exports include
--   SKU and resource metadata that this query relies on).
-- - Replace the table placeholder(s) below with your actual export table identifier,
--   for example: `my-billing-project.my_dataset.gcp_billing_export_v1_012345_YYYYMMDD` or
--   the wildcard export table pattern `my-billing-project.my_dataset.gcp_billing_export_v1_*`.
-- ------------------------------------------------------------
WITH
  bq_usage AS (
  SELECT
    cost,
    sku.description AS sku_desc,
    service.description AS service_desc,
    usage_start_time
  FROM
    `{{PROJECT_ID}}.{{DATASET}}.{{TABLE}}`
  WHERE
    service.description = 'BigQuery'
    AND usage_start_time BETWEEN TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    AND CURRENT_TIMESTAMP() )
SELECT
  activity,
  ROUND(SUM(cost), 2) AS total_cost_usd
FROM (
  SELECT
    cost,
    CASE
      WHEN LOWER(sku_desc) LIKE '%analysis%' THEN 'Query (Analysis)'
      WHEN LOWER(sku_desc) LIKE '%storage%' THEN 'Storage'
      WHEN LOWER(sku_desc) LIKE '%streaming insert%' THEN 'Streaming Inserts'
      WHEN LOWER(sku_desc) LIKE '%load job%' THEN 'Load Jobs'
      WHEN LOWER(sku_desc) LIKE '%copy%' THEN 'Copy Jobs'
      ELSE 'Other: ' || sku_desc
  END
    AS activity
  FROM
    bq_usage )
GROUP BY
  activity
ORDER BY
  total_cost_usd DESC;