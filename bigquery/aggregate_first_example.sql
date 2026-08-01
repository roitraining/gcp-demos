-- join at raw grain query
-- the question is "orders per state"; the join only exists to look up
-- each customer's state, but all 375M order rows arrive at the join
SELECT
  c.cust_state,
  COUNT(*) AS orders
FROM
  `roi-bq-demos.bq_demo_small.order` o
JOIN
  `roi-bq-demos.bq_demo_small.customer` c
ON
  o.cust_id = c.cust_id
GROUP BY
  cust_state
ORDER BY
  orders DESC

-- aggregate first query
-- collapse orders to one row per customer before the join, then let
-- the COUNT survive the join as SUM(n); same answer, far less work
WITH per_cust AS (
  SELECT
    cust_id,
    COUNT(*) AS n
  FROM
    `roi-bq-demos.bq_demo_small.order`
  GROUP BY
    cust_id
)
SELECT
  c.cust_state,
  SUM(pc.n) AS orders
FROM
  per_cust pc
JOIN
  `roi-bq-demos.bq_demo_small.customer` c
ON
  pc.cust_id = c.cust_id
GROUP BY
  cust_state
ORDER BY
  orders DESC
