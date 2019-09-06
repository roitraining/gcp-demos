 #!/bin/bash
bq query --use_legacy_sql=false --destination_table=roi-bq-demo:bq_demo.denorm 'SELECT
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
  `roi-bq-demo.bq_demo.customer` c
LEFT JOIN
  `roi-bq-demo.bq_demo.order` o
ON
  c.cust_id = o.cust_id
LEFT JOIN
  `roi-bq-demo.bq_demo.line_item` AS li
ON
  o.order_num = li.order_num
LEFT JOIN
  `roi-bq-demo.bq_demo.product` AS p
ON
  li.prod_code = p.prod_code'