-- This file contains a list of example queries illustrating the power and benefit of using BigQuery INFORMATION_SCHEMA views.

-- Use case: Identify top users by query volume and bytes processed in the last 7 days.
-- This query helps monitor user activity and analyze cost drivers, especially useful for environments with on-demand pricing.
-- It works by aggregating the total bytes processed and number of queries per user from the JOBS_BY_PROJECT view, filtered to the past week, and sorts the results to show the most active users.
SELECT
  user_email,
  SUM(total_bytes_processed) AS total_bytes_processed,
  COUNT(job_id) AS total_queries,
FROM
  `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE
  job_type = 'QUERY'
  AND creation_time BETWEEN TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY) AND CURRENT_TIMESTAMP()
GROUP BY
  user_email
ORDER BY
  total_bytes_processed DESC
LIMIT 10;


-- Use case: Analyze table storage efficiency and compression to optimize costs and identify tables that might benefit from physical storage pricing.
-- This query retrieves logical and physical storage metrics for each table, calculates compression ratios, and highlights tables with high or low compression.
-- It also computes the proportion of data stored long-term, helping you spot tables that may benefit from partitioning or clustering.
SELECT
  table_schema,
  table_name,
  total_logical_bytes,
  total_physical_bytes,
IF
  (total_logical_bytes = 0, 0, (1-ROUND(total_physical_bytes/total_logical_bytes, 2)))*100 AS compression_ratio,
  active_logical_bytes,
  long_term_logical_bytes,
 IF
  (total_logical_bytes = 0, 0, (1-ROUND(active_logical_bytes/total_logical_bytes, 2)))*100 AS long_term_ratio,
FROM
  `region-us.INFORMATION_SCHEMA.TABLE_STORAGE_BY_PROJECT`
ORDER BY
  compression_ratio DESC;


-- Use case: Identify recent queries that performed full table scans, which can be costly and indicate missing WHERE filters.
-- This query finds SELECT statements executed in the last 24 hours that do not contain a WHERE clause, highlighting queries likely to scan entire tables.
-- It helps pinpoint opportunities to optimize queries and reduce costs by adding filters or partitioning.
SELECT
  query,
  user_email,
  total_bytes_processed
FROM
  `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE
  job_type = 'QUERY'
  AND statement_type = 'SELECT'
  AND total_bytes_processed > 0
  AND creation_time BETWEEN TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR) AND CURRENT_TIMESTAMP()
  AND NOT REGEXP_CONTAINS(query, r'WHERE')
ORDER BY
  total_bytes_processed DESC
LIMIT 10;

-- Use case: Find tables that have not been accessed in the last 90 days to identify candidates for cleanup, archiving, or cost optimization.
-- This query combines job history and table metadata to determine the last time each table was queried, then filters for tables with no recent access.
WITH
  recent_access AS (
  SELECT
    rt.project_id AS project_id,
    rt.dataset_id AS dataset_id,
    rt.table_id AS table_name,
    MAX(j.creation_time) AS last_access_time
  FROM
    `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT` AS j
  CROSS JOIN
    UNNEST(j.referenced_tables) AS rt
  WHERE
    j.job_type = "QUERY"
    AND j.state = "DONE"
  GROUP BY
    project_id,
    dataset_id,
    table_name )
  -- 2) List all tables in the project and left-join access info
SELECT
  t.table_catalog AS project_id,
  t.table_schema AS dataset_id,
  t.table_name,
  r.last_access_time
FROM
  `region-us.INFORMATION_SCHEMA.TABLES` AS t
LEFT JOIN
  recent_access AS r
ON
  t.table_catalog = r.project_id
  AND t.table_schema = r.dataset_id
  AND t.table_name = r.table_name
  -- 3) Filter to those not accessed in the last 90 days (or never accessed)
WHERE
  COALESCE(r.last_access_time, TIMESTAMP '1970-01-01') < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
ORDER BY
  r.last_access_time;


-- Use case: Monitor recent slot usage for jobs to analyze resource consumption, do slot budgeting, allocate costs, etc..
-- This query lists jobs executed in the last hour in a given region/project that used slots, showing who ran them and how many slot milliseconds were consumed.
-- It helps identify users or jobs with high resource usage
SELECT
  creation_time,
  job_id,
  user_email,
  total_slot_ms,
FROM
  `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE
  creation_time BETWEEN TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR) AND CURRENT_TIMESTAMP()
  AND total_slot_ms > 0
ORDER BY
  total_slot_ms DESC;

-- Use case: Audit and document all view definitions in a project for governance, troubleshooting, or migration.
-- This query lists every view in the project/region along with its SQL definition, making it easy to review logic, dependencies, and ensure compliance.
SELECT
  table_schema,
  table_name,
  view_definition
FROM
  `region-us.INFORMATION_SCHEMA.VIEWS`
ORDER BY
  table_schema,
  table_name;