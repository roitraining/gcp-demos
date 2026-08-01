-- sales joined to price history query
-- generates its own data, so it bills 0 bytes
-- sales has 100,000 sales of 100 products; price_history has every
-- price each product has ever had (1,000 rows per product)
-- joining on prod_code alone matches each sale to EVERY historical
-- price, so the join emits 1,000x more rows than it should, and the
-- revenue total is inflated 1,000x
WITH sales AS (
  SELECT s AS sale_id, MOD(s, 100) AS prod_code
  FROM UNNEST(GENERATE_ARRAY(1, 100000)) AS s
),
price_history AS (
  SELECT MOD(p, 100) AS prod_code,
    DATE_ADD(DATE "2023-01-01", INTERVAL DIV(p, 100) DAY) AS effective_date,
    ROUND(10 + MOD(p, 90) + MOD(p, 7) / 10, 2) AS price
  FROM UNNEST(GENERATE_ARRAY(1, 100000)) AS p
)
SELECT
  COUNT(*) AS output_rows,
  ROUND(SUM(price), 2) AS total_revenue
FROM sales
JOIN price_history USING (prod_code)

-- sales joined to current price query
-- the fix: reduce price_history to one row per product (the price
-- currently in effect) before joining, so each sale matches one price
WITH sales AS (
  SELECT s AS sale_id, MOD(s, 100) AS prod_code
  FROM UNNEST(GENERATE_ARRAY(1, 100000)) AS s
),
price_history AS (
  SELECT MOD(p, 100) AS prod_code,
    DATE_ADD(DATE "2023-01-01", INTERVAL DIV(p, 100) DAY) AS effective_date,
    ROUND(10 + MOD(p, 90) + MOD(p, 7) / 10, 2) AS price
  FROM UNNEST(GENERATE_ARRAY(1, 100000)) AS p
),
current_price AS (
  SELECT
    prod_code,
    ARRAY_AGG(price ORDER BY effective_date DESC LIMIT 1)[OFFSET(0)] AS price
  FROM price_history
  GROUP BY prod_code
)
SELECT
  COUNT(*) AS output_rows,
  ROUND(SUM(price), 2) AS total_revenue
FROM sales
JOIN current_price USING (prod_code)
