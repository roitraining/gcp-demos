-- populate arrays explicitly
SELECT
  "row1" AS row_id,
  [1,
  2,
  3,
  4] AS num_array
UNION ALL
SELECT
  "row2" AS row_id,
  [2,
  4,
  8,
  16,
  32] AS num_array
UNION ALL
SELECT
  "row3" AS row_id,
  [5,
  10] AS num_array

-- populate arrays using array_agg
WITH
  c AS (
  SELECT
    cust_id,
    cust_name,
    cust_zip
  FROM
    `roi-bq-demos.bq_demo.cp`
  WHERE
    cust_state = "AK")
SELECT
  cust_name,
  ARRAY_AGG(order_num) as orders
FROM
  c
JOIN
  `roi-bq-demos.bq_demo.order` o
ON
  o.cust_id = c.cust_id
GROUP BY
  c.cust_name

-- report array length
SELECT
  `commit`,
  ARRAY_LENGTH(difference) AS arr_len,
  difference
FROM
  `bigquery-public-data.github_repos.commits`
WHERE
  author.email LIKE "%jwdavis.me"
ORDER BY
  arr_len DESC
LIMIT
  5

-- find by array length
SELECT
  author,
  difference
FROM
  `bigquery-public-data.github_repos.commits`
WHERE
  array_length(difference) = 5
LIMIT 10

-- select basic array
SELECT
  [1,
  2,
  3,
  4] AS num_array

-- select table from array
SELECT
  *
FROM
  UNNEST ( [1, 2, 3, 4]) AS num

-- calculate average of array
SELECT
    AVG(num) AS avg_num
FROM
  UNNEST ( [1, 2, 3, 4]) AS num

-- basic correlated cross join
WITH
  arrays AS (
  SELECT
    "row1" AS row_id,
    [1,
    2,
    3,
    4] AS num_array
  UNION ALL
  SELECT
    "row2" AS row_id,
    [2,
    4,
    8,
    16,
    32] AS num_array)
SELECT
  row_id,
  num
FROM
  arrays
CROSS JOIN
  UNNEST(num_array) AS num

-- find elements where num=2
WITH
  arrays AS (
  SELECT
    "row1" AS row_id,
    [1,
    2,
    3,
    4] AS num_array
  UNION ALL
  SELECT
    "row2" AS row_id,
    [2,
    4,
    8,
    16,
    32] AS num_array)
SELECT
  row_id,
  num
FROM
  arrays
CROSS JOIN
  UNNEST(num_array) AS num
WHERE
  num=2

-- find rows where num=2
WITH
  arrays AS (
  SELECT
    "row1" AS row_id,
    [1,
    2,
    3,
    4] AS num_array
  UNION ALL
  SELECT
    "row2" AS row_id,
    [2,
    4,
    8,
    16,
    32] AS num_array)
SELECT
  row_id,
  num_array
FROM
  arrays
CROSS JOIN
  UNNEST(num_array) AS num
WHERE
  num=2

-- find commits that touched a specific file - take 1
SELECT
  author,
  difference
FROM
  `bigquery-public-data.github_repos.commits`,
  unnest(difference) as files
WHERE
  files.new_path = "courses/data_analysis/lab2/python/is_popular.py"

-- find commits that touched a specific file - take 2
SELECT
  author,
  difference
FROM
  `bigquery-public-data.github_repos.commits`
WHERE
  "courses/data_analysis/lab2/python/is_popular.py" in (select f.new_path from unnest(difference) as f)

-- find commits that touched a specific file - take 3
SELECT
  author,
  difference
FROM
  `bigquery-public-data.github_repos.commits`
WHERE
  EXISTS (
  SELECT
    *
  FROM
    UNNEST(difference) AS f
  WHERE
    f.new_path="courses/data_analysis/lab2/python/is_popular.py")