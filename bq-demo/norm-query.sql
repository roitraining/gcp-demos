WITH
  joined AS (
  SELECT
    c.cust_zip,
    o.o_num,
    li.oline_qty * p.prod_price AS line_item_subtotal
  FROM
    `roi-bq-demo.bq_benchmark_tables.customer` c
  LEFT JOIN
    `roi-bq-demo.bq_benchmark_tables.order` o
  ON
    o.o_cust_num = c.cust_num
  LEFT JOIN
    `roi-bq-demo.bq_benchmark_tables.order_line_item` li
  ON
    o.o_num = li.oline_order_num
  LEFT JOIN
    `roi-bq-demo.bq_benchmark_tables.product` p
  ON
    p.prod_code = li.oline_prod_code
  WHERE
    o.o_date >= "2018-03-01"
    AND o.o_date <= "2018-03-31" ),
  totals AS (
  SELECT
    cust_zip,
    o_num,
    SUM(line_item_subtotal) AS order_total
  FROM
    joined
  GROUP BY
    o_num,
    cust_zip)
SELECT
  zip,
  SUM(order_total) as zip_sales
FROM
  totals
GROUP BY
  cust_zip



WITH
  joined AS (
  SELECT
    c.cust_zip,
    o.o_num,
    li.oline_qty * p.prod_price AS line_item_subtotal
  FROM
    `roi-bq-demo.bq_benchmark_tables.customer` c
  LEFT JOIN
    `roi-bq-demo.bq_benchmark_tables.order` o
  ON
    o.o_cust_num = c.cust_num
  LEFT JOIN
    `roi-bq-demo.bq_benchmark_tables.order_line_item` li
  ON
    o.o_num = li.oline_order_num
  LEFT JOIN
    `roi-bq-demo.bq_benchmark_tables.product` p
  ON
    p.prod_code = li.oline_prod_code
  WHERE
    o.o_date >= "2018-03-01"
    AND o.o_date <= "2018-03-31" )
SELECT
  cust_zip,
  SUM(line_item_subtotal) as zip_sales
FROM
  joined
GROUP BY
  cust_zip