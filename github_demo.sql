#standardSQL
#search based on array length
#display full struct and array of struct
SELECT
  author,
  difference
FROM
  `bigquery-public-data.github_repos.commits`
WHERE
  array_length(difference) = 5
LIMIT 10

#standardSQL
#search based on array length
#create separate columns from struct properties
SELECT
  author.email,
  difference
FROM
  `bigquery-public-data.github_repos.commits`
WHERE
  array_length(difference) = 5
LIMIT 10

#standardSQL
#show correlated cross join and unnest
#this one row per email/file combo
#but also include the entire array for each output row
WITH
  sample AS (
  SELECT
    author.email,
    difference
  FROM
    `bigquery-public-data.github_repos.commits`
  WHERE
    ARRAY_LENGTH(difference) = 5
  LIMIT
    1)
SELECT
  email,
  difference,
  diff.new_path as path
from
  sample,
  unnest(difference) as diff

#standardSQL
#show correlated cross join and unnest
#this drop the difference column with the array
WITH
  sample AS (
  SELECT
    author.email,
    difference
  FROM
    `bigquery-public-data.github_repos.commits`
  WHERE
    ARRAY_LENGTH(difference) = 5
  LIMIT
    1)
SELECT
  email,
  diff.new_path as path
from
  sample,
  unnest(difference) as diff

#standardSQL
#find commits where a particular file was touched
#this shows searching on values within an array
#by using correlated cross join and filter
SELECT
  author,
  difference
FROM
  `bigquery-public-data.github_repos.commits`,
  unnest(difference) as files
WHERE
  files.new_path = "courses/data_analysis/lab2/python/is_popular.py"

#standardSQL
#this also shows searching on values within an array
#this time using subquery in where clause
SELECT
  author,
  difference
FROM
  `bigquery-public-data.github_repos.commits`
WHERE
  "courses/data_analysis/lab2/python/is_popular.py" in (select f.new_path from unnest(difference) as f)

#standardSQL
#this is by far the fastest way of the three to search on values in array
#this avoids the cross join of #1. EXISTS is faster than IN
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