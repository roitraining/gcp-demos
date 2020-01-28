 #!/bin/bash

 read -p "project for normalized data: " norm_project 
 read -p "project for dervied tables: " derived_project
 read -p "source bucket: " bucket

bq load --source_format=CSV $norm_project:bq_demo.customer gs://$bucket/bq-demo/customer* ./customer_schema.json
bq load --source_format=CSV $norm_project:bq_demo.order gs://$bucket/bq-demo/order* ./order_schema.json
bq load --source_format=CSV $norm_project:bq_demo.product gs://$bucket/bq-demo/product* ./product_schema.json
bq load --source_format=CSV $norm_project:bq_demo.line_item gs://$bucket/bq-demo/line_item* ./line_item_schema.json

bq query --use_legacy_sql=false --destination_table=$derived_project:bq_demo.denorm '
SELECT
  c.*,
  o.order_num as order_num, 
  order_date,
  line_item_num, 
  li.prod_code as prod_code, 
  qty,
  prod_name, 
  prod_desc, 
  prod_price
FROM
  '"\`$norm_project.bq_demo.customer\`"' c
LEFT JOIN
  '"\`$norm_project.bq_demo.order\`"' o
ON
  c.cust_id = o.cust_id
LEFT JOIN
  '"\`$norm_project.bq_demo.line_item\`"' AS li
ON
  o.order_num = li.order_num
LEFT JOIN
  '"\`$norm_project.bq_demo.product\`"' AS p
ON
  li.prod_code = p.prod_code'

bq query --use_legacy_sql=false --destination_table=$derived_project:bq_demo.nested_once '
WITH
  dlow AS (
  SELECT
    *
  FROM
    '"\`$derived_project.bq_demo.denorm\`"'
)
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
      prod_price)) as line_items
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
  cust_id'

bq query --use_legacy_sql=false \
--destination_table $derived_project:bq_demo.table_nested_partitioned \
--time_partitioning_field order_date \
'SELECT * FROM '"\`$derived_project.bq_demo.nested_once\`"

bq query --use_legacy_sql=false 'CREATE TABLE 
'"\`$derived_project.bq_demo.table_nested_partitioned_clustered\`"' 
PARTITION BY order_date 
CLUSTER BY cust_zip AS 
SELECT * FROM '"\`$derived_project.bq_demo.nested_once\`"

bq query --use_legacy_sql=false \
--destination_table=$derived_project:bq_demo.nested_twice '
WITH
  dlow AS (
  SELECT
    *
  FROM
    '"\`$derived_project.bq_demo.denorm\`"' ),
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
    cust_name'