#standardSQL
#search based on array length
#display full struct and array of struct
SELECT
  author,
  difference
FROM
  `bigquery-public-data.github_repos.commits`
WHERE
  EXTRACT(YEAR
  FROM
    author.date)=2016
  AND array_length(difference) = 5
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
  EXTRACT(YEAR
  FROM
    author.date)=2016
  AND array_length(difference) = 5
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
    EXTRACT(YEAR
    FROM
      author.date)=2016
    AND ARRAY_LENGTH(difference) = 5
  LIMIT
    1)
SELECT
  email,
  date,
  diff.new_path as path
from
  sample,
  unnest(difference) as diff

