 #!/bin/bash
bq query --use_legacy_sql=false --destination_table=roi-bq-demo:bq_demo.nested_once '
WITH
  dlow AS (
  SELECT
    *
  FROM
    `roi-bq-demo.bq_demo.denorm`
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
--destination_table roi-bq-demo:bq_demo.table_nested_partitioned \
--time_partitioning_field order_date \
'SELECT * FROM `roi-bq-demo.bq_demo.nested_once`'

bq query --use_legacy_sql=false 'CREATE TABLE 
`roi-bq-demo.bq_demo.table_nested_partitioned_clustered` 
PARTITION BY order_date 
CLUSTER BY order_date, cust_zip AS 
SELECT * FROM `roi-bq-demo.bq_demo.nested_once`'


