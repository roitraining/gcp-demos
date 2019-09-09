 #!/bin/bash

# bq load --source_format=CSV $DEVSHELL_PROJECT_ID:bq_demo.customer gs://$DEVSHELL_PROJECT_ID-bq-demo/customer* ./customer_schema.json
# bq load --source_format=CSV $DEVSHELL_PROJECT_ID:bq_demo.order gs://$DEVSHELL_PROJECT_ID-bq-demo/order* ./order_schema.json
# bq load --source_format=CSV $DEVSHELL_PROJECT_ID:bq_demo.product gs://$DEVSHELL_PROJECT_ID-bq-demo/product* ./product_schema.json
# bq load --source_format=CSV $DEVSHELL_PROJECT_ID:bq_demo.line_item gs://$DEVSHELL_PROJECT_ID-bq-demo/line_item* ./line_item_schema.json

bq query --use_legacy_sql=false --destination_table=$DEVSHELL_PROJECT_ID:bq_demo.denorm 'SELECT
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
  '"\`$DEVSHELL_PROJECT_ID.bq_demo.customer\`"' c
LEFT JOIN
  '"\`$DEVSHELL_PROJECT_ID.bq_demo.order\`"' o
ON
  c.cust_id = o.cust_id
LEFT JOIN
  '"\`$DEVSHELL_PROJECT_ID.bq_demo.line_item\`"' AS li
ON
  o.order_num = li.order_num
LEFT JOIN
  '"\`$DEVSHELL_PROJECT_ID.bq_demo.product\`"' AS p
ON
  li.prod_code = p.prod_code'

bq query --use_legacy_sql=false --destination_table=$DEVSHELL_PROJECT_ID:bq_demo.nested_once '
WITH
  dlow AS (
  SELECT
    *
  FROM
    '"\`$DEVSHELL_PROJECT_ID.bq_demo.denorm\`"'
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
--destination_table $DEVSHELL_PROJECT_ID:bq_demo.table_nested_partitioned \
--time_partitioning_field order_date \
'SELECT * FROM '"\`$DEVSHELL_PROJECT_ID.bq_demo.nested_once\`"

bq query --use_legacy_sql=false 'CREATE TABLE 
'"\`$DEVSHELL_PROJECT_ID.bq_demo.table_nested_partitioned_clustered\`"' 
PARTITION BY order_date 
CLUSTER BY order_date, cust_zip AS 
SELECT * FROM '"\`$DEVSHELL_PROJECT_ID.bq_demo.nested_once\`"

bq query --use_legacy_sql=false \
--destination_table=$DEVSHELL_PROJECT_ID:bq_demo.nested_twice '
WITH
  dlow AS (
  SELECT
    *
  FROM
    '"\`$DEVSHELL_PROJECT_ID.bq_demo.denorm\`"' ),
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