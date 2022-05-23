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