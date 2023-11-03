CREATE OR REPLACE TABLE
  `bq_demo.denorm` AS (
SELECT
  c.*,
  o.order_num AS order_num,
  order_date,
  line_item_num,
  li.prod_code AS prod_code,
  qty,
  prod_name,
  prod_desc,
  prod_price
FROM
  `roi-bq-demos.bq_demo.customer` c
LEFT JOIN
  `roi-bq-demos.bq_demo.order` o
ON
  c.cust_id = o.cust_id
LEFT JOIN
  `roi-bq-demos.bq_demo.line_item` AS li
ON
  o.order_num = li.order_num
LEFT JOIN
  `roi-bq-demos.bq_demo.product` AS p
ON
  li.prod_code = p.prod_code);

CREATE OR REPLACE TABLE
  `bq_demo.nested_once` AS (
  WITH
    dlow AS (
    SELECT
      *
    FROM
      `bq_demo.denorm` )
  SELECT
    cust_id,
    cust_name,
    cust_address,
    cust_state,
    cust_zip,
    cust_email,
    cust_phone,
    order_num,
    order_date,
    ARRAY_AGG( STRUCT(line_item_num,
        prod_code,
        qty,
        prod_name,
        prod_desc,
        prod_price)) AS line_items
  FROM
    dlow
  GROUP BY
    order_num,
    order_date,
    cust_phone,
    cust_email,
    cust_zip,
    cust_state,
    cust_address,
    cust_name,
    cust_id);

CREATE OR REPLACE TABLE
  `bq_demo.table_nested_partitioned`
PARTITION BY
  order_date AS (
SELECT
  *
FROM
  `bq_demo.nested_once`);

CREATE OR REPLACE TABLE
  `bq_demo.table_nested_partitioned_clustered`
PARTITION BY
  order_date
CLUSTER BY
  cust_zip AS (
SELECT
  *
FROM
  `bq_demo.nested_once`)