 #!/bin/bash
bq query --use_legacy_sql=false --destination_table=roi-bq-demo:bq_demo.nested_twice '
WITH
  dlow AS (
  SELECT
    *
  FROM
    `roi-bq-demo.bq_demo.denorm` ),
  orders AS (
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
    cust_id)
  SELECT
    cust_phone,
    cust_email,
    cust_zip,
    cust_state,
    cust_address,
    cust_name,
    cust_id,
    ARRAY_AGG( STRUCT( order_num,
        order_date,
        line_items )) AS orders
  FROM
    orders
  GROUP BY
    cust_id,
    cust_phone,
    cust_email,
    cust_zip,
    cust_state,
    cust_address,
    cust_name
'