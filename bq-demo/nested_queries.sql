#standardSQL
#find sales/zip for august from nested_once table
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `roi-bq-demo.bq_demo.nested_once`,
    unnest(line_items)
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


#standardSQL
#find sales/zip for august from nested/partitioned
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `roi-bq-demo.bq_demo.table_nested_partitioned`,
    unnest(line_items)
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

#standardSQL
#find sales/zip for all from nested/partitioned
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `roi-bq-demo.bq_demo.table_nested_partitioned`,
    unnest(line_items)
SELECT
  cust_zip,
  SUM(line_item_subtotal) as zip_sales
FROM
  orders
GROUP BY
  cust_zip
order by 
  zip_sales desc

#standardSQL
#find sales/zip for all from nested/partitioned/clustered
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `roi-bq-demo.bq_demo.table_nested_partitioned_clustered`,
    unnest(line_items)
SELECT
  cust_zip,
  SUM(line_item_subtotal) as zip_sales
FROM
  orders
GROUP BY
  cust_zip
order by 
  zip_sales desc