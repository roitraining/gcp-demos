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
  author.date,
  difference
FROM
  `bigquery-public-data.github_repos.commits`
WHERE
  array_length(difference) = 5
LIMIT 10

#standardSQL
#show correlated cross join and unnest
WITH
  sample AS (
  SELECT
    author.email,
    author.date,
    difference
  FROM
    `bigquery-public-data.github_repos.commits`
  WHERE
    ARRAY_LENGTH(difference) = 5
  LIMIT
    1)
SELECT
  email,
  date,
  diff.new_path as path
from
  sample,
  unnest(difference) as diff

#standardSQL
#find commits where a particular file was touched
#this shows searching on values within an array
SELECT
  author,
  difference
FROM
  `bigquery-public-data.github_repos.commits`,
  unnest(difference) as files
WHERE
  files.new_path = "courses/data_analysis/lab2/python/is_popular.py"


SELECT
  author,
  difference
FROM
  `bigquery-public-data.github_repos.commits`
WHERE
  "courses/data_analysis/lab2/python/is_popular.py" in (select f.new_path from unnest(difference) as f)


#standardSQL
#alternative approach to above query
SELECT
  author,
  difference
FROM
  `bigquery-public-data.github_repos.commits`
WHERE
  exists (select * from unnest(difference) as f where f.name="courses/data_analysis/lab2/python/is_popular.py")