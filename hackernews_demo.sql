# get simple results
SELECT
  DATE(time_ts) AS day,
  title,
  score
FROM
  `bigquery-public-data.hacker_news.stories`
order by
  day desc, score desc

# filter nulls
SELECT
  DATE(time_ts) AS day,
  title,
  score
FROM
  `bigquery-public-data.hacker_news.stories`
WHERE
  score IS NOT NULL
  AND title IS NOT NULL
order by
  day desc, score desc

# create struct
SELECT
  DATE(time_ts) AS day,
  STRUCT (title,
    score) AS top_articles
FROM
  `bigquery-public-data.hacker_news.stories`
WHERE
  score IS NOT NULL
  AND title IS NOT NULL
order by
  day desc, score desc
Limit
  300

# leverage window functions to get ranking
SELECT
  DATE(time_ts) AS day,
  ROW_NUMBER() OVER (PARTITION BY DATE(time_ts)
  ORDER BY
    score DESC) AS row,
  STRUCT (title,
    score) AS top_articles
FROM
  `bigquery-public-data.hacker_news.stories`
WHERE
  score IS NOT NULL
  AND title IS NOT NULL
order by
  day desc,
  row
limit 
  100

# simple array agg
SELECT
  day,
  ARRAY_AGG(top_articles) AS top_articles
FROM (
  SELECT
    DATE(time_ts) AS day,
    STRUCT (title,
      score) AS top_articles
  FROM
    `bigquery-public-data.hacker_news.stories`
  WHERE
    score IS NOT NULL
    AND title IS NOT NULL
  Limit
    100000)
GROUP BY
  day
ORDER BY
  day DESC

# the whole shebang
SELECT
  day,
  ARRAY_AGG(top_articles) AS top_articles
FROM (
  SELECT
    DATE(time_ts) AS day,
    ROW_NUMBER() OVER (PARTITION BY DATE(time_ts)
    ORDER BY
      score DESC) AS row,
    STRUCT (title,
      score) AS top_articles
  FROM
    `bigquery-public-data.hacker_news.stories`
  WHERE
    score IS NOT NULL
    AND title IS NOT NULL)
WHERE
  row <=5
GROUP BY
  day
ORDER BY
  day DESC
limit
  100