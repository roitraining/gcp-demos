-- find sales/zip for march
-- base normalized tables
SELECT
  c.cust_zip,
  SUM(li.qty * p.prod_price) AS zip_sales
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
  c.cust_zip
ORDER BY
  zip_sales DESC

-- find sales/zip for march
-- normalized tables with order_part table
SELECT
  c.cust_zip,
  SUM(li.qty * p.prod_price) AS zip_sales
FROM
  `roi-bq-demos.bq_demo.order_part` o
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
  c.cust_zip
ORDER BY
  zip_sales DESC