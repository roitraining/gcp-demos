#Run these within a QLabs projects
#Run the approx first
#When it's done, run the exact
#Compare times and % difference

#First query - approx
#StandardSQL
#wiki 1M
SELECT
  approx_count_distinct(title) AS articles
FROM
  `bigquery-samples.wikipedia_benchmark.Wiki100B`
ORDER BY
  articles DESC

#First query - exact
#StandardSQL
#wiki 1M
SELECT
  COUNT(distinct title) AS articles
FROM
  `bigquery-samples.wikipedia_benchmark.Wiki100B`
ORDER BY
  articles DESC
