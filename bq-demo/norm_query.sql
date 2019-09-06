WITH
  joined AS (
  SELECT
    c.cust_zip,
    o.order_num,
    li.qty * p.prod_price AS line_item_subtotal
  FROM
    `roi-bq-demo.bq_demo.customer` c
  LEFT JOIN
    `roi-bq-demo.bq_demo.order` o
  ON
    o.cust_id = c.cust_id
  LEFT JOIN
    `roi-bq-demo.bq_demo.line_item` li
  ON
    o.order_num = li.order_num
  LEFT JOIN
    `roi-bq-demo.bq_demo.product` p
  ON
    p.prod_code = li.prod_code
  WHERE
    o.order_date >= "2018-03-01"
    AND o.order_date <= "2018-03-31" )
SELECT
  cust_zip,
  SUM(line_item_subtotal) as zip_sales
FROM
  joined
GROUP BY
  cust_zip
order BY 
  zip_sales desc