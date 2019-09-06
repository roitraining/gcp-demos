#standardSQL
#find sales/zip for august
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `roi-bq-demo.bq_demo.denorm`
  WHERE
    order_date >= "2018-03-01"
    AND order_date <= "2018-03-31")
SELECT
  cust_zip,
  SUM(line_item_subtotal) as zip_sales
FROM
  orders
GROUP BY
  cust_zip
order by 
  zip_sales desc