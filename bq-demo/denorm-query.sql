WITH
  joined AS (
  SELECT
    cust_zip,
    prod_price * oline_qty AS line_item_subtotal
  FROM
    `roi-bq-demo.bq_benchmark_tables_denorm.table_denorm`
  WHERE
    o_date >= "2018-03-01"
    AND o_date <= "2018-03-31")
SELECT
  cust_zip,
  SUM(line_item_subtotal)
FROM
  joined
GROUP BY
  cust_zip