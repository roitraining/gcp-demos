-- load monday query
-- same job the console and bq load produce, expressed in SQL; the column
-- list pins the schema the way --schema did on the command line
LOAD DATA INTO class.usage_sql (
  meeting_id STRING,
  user_id STRING,
  minutes INT64,
  event_date DATE
)
FROM FILES (
  format = 'CSV',
  skip_leading_rows = 1,
  uris = ['gs://jwd-gcp-demos/ingest_demo/daily/usage_2026-07-20.csv']
)

-- load tuesday query
-- the table exists now, so no column list is needed; LOAD DATA INTO
-- appends, LOAD DATA OVERWRITE would replace
LOAD DATA INTO class.usage_sql
FROM FILES (
  format = 'CSV',
  skip_leading_rows = 1,
  uris = ['gs://jwd-gcp-demos/ingest_demo/daily/usage_2026-07-21.csv']
)

-- verify query
SELECT
  event_date,
  COUNT(*) AS meetings,
  SUM(minutes) AS total_minutes
FROM class.usage_sql
GROUP BY event_date
ORDER BY event_date
