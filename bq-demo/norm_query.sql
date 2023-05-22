WITH
  march_orders AS (
    select 
      order_num,
      cust_id
    FROM  
      `<project-id>.bq_demo.order` o
    WHERE 
      o.order_date >= "2018-03-01"
      AND o.order_date <= "2018-03-31" ),
  joined AS (
  SELECT
    c.cust_zip,
    o.order_num,
    li.qty * p.prod_price AS line_item_subtotal
  FROM
    `<project-id>.bq_demo.line_item` li
  JOIN
    march_orders o
  ON
    o.order_num = li.order_num
  JOIN
    `<project-id>.bq_demo.customer` c
  ON
    o.cust_id = c.cust_id
  JOIN
    `<project-id>.bq_demo.product` p
  ON
    p.prod_code = li.prod_code)
SELECT
  cust_zip,
  SUM(line_item_subtotal) as zip_sales
FROM
  joined
GROUP BY
  cust_zip
order BY 
  zip_sales desc