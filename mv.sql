-- this is for reference; cannot be run unless you're an admin on dataset
CREATE MATERIALIZED VIEW
  roi-bq-demos.bq_demo.order_mv AS
SELECT
  cust_zip,
  order_date,
  count(*) as orders
FROM
  `roi-bq-demos.bq_demo.customer` c
JOIN
  `roi-bq-demos.bq_demo.order` o
ON
  o.cust_id= c.cust_id
GROUP BY
  order_date,
  cust_zip

-- query against materialized view
SELECT
  *
FROM
  `roi-bq-demos.bq_demo.order_mv`
WHERE
  cust_zip<2000

-- query against original tables that automatically uses the materialized view
SELECT
  cust_zip,
  order_date,
  COUNT(*) AS orders
FROM
  `roi-bq-demos.bq_demo.customer` c
JOIN
  `roi-bq-demos.bq_demo.order` o
ON
  o.cust_id = c.cust_id
WHERE
  cust_zip<2000
GROUP BY
  order_date,
  cust_zip