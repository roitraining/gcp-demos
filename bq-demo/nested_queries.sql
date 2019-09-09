#standardSQL
#find sales/zip for march from nested_once table
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `bq_demo.nested_once`,
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
#find sales/zip for march from nested/partitioned
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `bq_demo.table_nested_partitioned`,
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
#find sales/zip for 6 months from nested/partitioned
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `bq_demo.table_nested_partitioned`,
    unnest(line_items)
  WHERE
    order_date >= "2018-01-01"
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
#find sales/zip for 6 months from nested/partitioned/clustered
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `bq_demo.table_nested_partitioned_clustered`,
    unnest(line_items)
  WHERE
    order_date >= "2018-01-01"
    AND order_date <= "2018-06-30")
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
#find sales/zip for march from nested_twice table
SELECT
  cust_name,
  order_num,
  li
FROM (
  SELECT
    cust_name,
    order_num,
    orderinfo
  FROM
    `bq_demo.nested_twice`,
    UNNEST(orders) AS orderinfo
  WHERE
    order_date >= "2018-03-01"
    AND order_date <= "2018-03-31"
  LIMIT
    100),
  UNNEST(orderinfo.line_items) AS li