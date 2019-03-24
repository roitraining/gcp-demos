WITH
  denorm_line_items AS (
  SELECT
    *
  FROM
    `roi-bq-demo.bq_benchmark_tables.order_line_item` AS li
  LEFT JOIN
    `roi-bq-demo.bq_benchmark_tables.product` AS p
  ON
    p.prod_code = li.oline_prod_code)
SELECT
  c.cust_num,
  c.cust_name,
  c.cust_address,
  c.cust_state,
  c.cust_zip,
  c.cust_email,
  c.cust_phone
  o.o_num,
  o.o_cust_num,
  o.o_date,
  ARRAY_AGG(STRUCT(
      dli.oline_order_num,
      dli.oline_line_item_num,
      dli.oline_prod_code,
      dli.oline_qty,
      dli.prod_code,
      dli.prod_name,
      dli.prod_desc,
      dli.prod_price
      )) as line_items
FROM
  `roi-bq-demo.bq_benchmark_tables.customer` c
LEFT JOIN
  `roi-bq-demo.bq_benchmark_tables.order` o
ON
  o_cust_num = c.cust_num
LEFT JOIN
  denorm_line_items dli
ON
  o.o_num = dli.oline_order_num
GROUP BY
  o.o_num,
  o.o_cust_num,
  o.o_date,
  c.cust_num,
  c.cust_name,
  c.cust_address,
  c.cust_state,
  c.cust_zip,
  c.cust_email,
  c.cust_phone