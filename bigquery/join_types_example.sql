-- broadcast join query
-- product has only 10,000 rows, so BigQuery copies the whole table
-- to every worker and joins 3.75B line items in place during their scan
SELECT
  p.prod_name,
  SUM(li.qty) AS units
FROM
  `roi-bq-demos.bq_demo_small.line_item` li
JOIN
  `roi-bq-demos.bq_demo_small.product` p
ON
  li.prod_code = p.prod_code
GROUP BY
  p.prod_name
ORDER BY
  units DESC
LIMIT 10

-- hash join query
-- customer is too big to copy to every worker, so both tables are
-- shuffled by the join key before any joining happens
SELECT
  c.cust_state,
  COUNT(*) AS orders
FROM
  `roi-bq-demos.bq_demo_small.order` o
JOIN
  `roi-bq-demos.bq_demo_small.customer` c
ON
  o.cust_id = c.cust_id
GROUP BY
  cust_state
ORDER BY
  orders DESC
