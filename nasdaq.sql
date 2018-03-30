SELECT
  start_date AS date,
  symbol,
  MAX(ask_price) AS max_price,
  COUNT(ask_price) AS vol
FROM
  `bigquery-samples.nasdaq_stock_quotes.quotes`
GROUP BY
  start_date,
  symbol
ORDER BY
  symbol,
  date