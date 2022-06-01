-- standardSQL
-- find sales/zip for march from nested_once table
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `<project-id>.bq_demo.nested_once`,
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


-- standardSQL
-- find sales/zip for march from nested/partitioned
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `<project-id>.bq_demo.table_nested_partitioned`,
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

-- standardSQL
-- find sales for 6 months in 8754 from nested
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `<project-id>.bq_demo.nested_once`,
    UNNEST(line_items)
  WHERE
    order_date >= "2018-01-01"
    AND order_date <= "2018-06-30"
    AND cust_zip=8754)
  SELECT
    cust_zip,
    SUM(line_item_subtotal) AS zip_sales
  FROM
    orders
  GROUP BY
    cust_zip
  ORDER BY
    zip_sales DESC

-- standardSQL
-- find for 6 months in 8754 from nested/partitioned
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `<project-id>.bq_demo.table_nested_partitioned`,
    UNNEST(line_items)
  WHERE
    order_date >= "2018-01-01"
    AND order_date <= "2018-06-30"
    AND cust_zip=8754)
  SELECT
    cust_zip,
    SUM(line_item_subtotal) AS zip_sales
  FROM
    orders
  GROUP BY
    cust_zip
  ORDER BY
    zip_sales DESC

-- standardSQL
-- find for 6 months in 8754 from nested/partitioned/clustered
WITH
  orders AS (
  SELECT
    cust_zip,
    prod_price * qty AS line_item_subtotal
  FROM
    `<project-id>.bq_demo.table_nested_partitioned_clustered`,
    UNNEST(line_items)
  WHERE
    order_date >= "2018-01-01"
    AND order_date <= "2018-06-30"
    AND cust_zip=8754)
  SELECT
    cust_zip,
    SUM(line_item_subtotal) AS zip_sales
  FROM
    orders
  GROUP BY
    cust_zip
  ORDER BY
    zip_sales DESC