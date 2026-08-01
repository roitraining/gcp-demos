-- heavyweight query
-- joins and aggregation across the full normalized dataset
SELECT
  c.cust_state,
  SUM(li.qty * p.prod_price) AS state_sales
FROM
  `roi-bq-demos.bq_demo.order` o
JOIN
  `roi-bq-demos.bq_demo.line_item` li
ON
  o.order_num = li.order_num
JOIN
  `roi-bq-demos.bq_demo.customer` c
ON
  o.cust_id = c.cust_id
JOIN
  `roi-bq-demos.bq_demo.product` p
ON
  p.prod_code = li.prod_code
WHERE
  o.order_date >= "2018-03-01"
  AND o.order_date <= "2018-03-31"
GROUP BY
  c.cust_state
ORDER BY
  state_sales DESC

-- lightweight query
-- single-table scan with a simple aggregation
SELECT
  cust_state,
  COUNT(*) AS customer_count
FROM
  `roi-bq-demos.bq_demo.customer`
GROUP BY
  cust_state
ORDER BY
  customer_count DESC
