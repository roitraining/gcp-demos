-- CAUTION: these queries are meant to be pasted into the BigQuery
-- editor so you can read the estimate in the query validator (lower
-- left of the editor). Do NOT run the select star query; it would
-- cost more than $15 on demand.

-- select star query
-- touches every column: reads ~2.4 TB
SELECT *
FROM `bigquery-public-data.github_repos.contents`

-- two columns query
-- touches only two columns: reads ~13 GB
SELECT
  id,
  size
FROM `bigquery-public-data.github_repos.contents`

-- filtered two columns query
-- the WHERE column counts too: reads slightly more than the two columns query
SELECT
  id,
  size
FROM `bigquery-public-data.github_repos.contents`
WHERE binary = FALSE

-- select star except query
-- nearly all the columns, skipping the giant blob: reads ~15.5 GB
SELECT * EXCEPT(content)
FROM `bigquery-public-data.github_repos.contents`
