# wiki 1M
SELECT
  title,
  SUM(views) AS views
FROM
  `bigquery-samples.wikipedia_benchmark.Wiki1M`
WHERE
  REGEXP_CONTAINS(title,".*Davis.*")
GROUP BY
  title
ORDER BY
  views DESC
