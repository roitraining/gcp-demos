-- These queries are meant to be pasted into the BigQuery editor so you
-- can read the estimate in the query validator (lower left of the
-- editor). There is no need to run any of them.

-- unpartitioned table query
-- no partitions to skip: reads ~112 GB
SELECT COUNT(DISTINCT cust_id) AS customers
FROM `roi-bq-demos.bq_demo.order`
WHERE order_date >= "2018-03-01"
  AND order_date <= "2018-03-31"

-- partitioned table query
-- bare partition column compared to constants: reads ~9.3 GB
SELECT COUNT(DISTINCT cust_id) AS customers
FROM `roi-bq-demos.bq_demo.order_part`
WHERE order_date >= "2018-03-01"
  AND order_date <= "2018-03-31"

-- broken partition filter query
-- same table, same rows, but the partition column is wrapped in a
-- function, so no partition can be skipped: reads ~112 GB
SELECT COUNT(DISTINCT cust_id) AS customers
FROM `roi-bq-demos.bq_demo.order_part`
WHERE FORMAT_DATE("%Y%m", order_date) = "201803"

-- unclustered table query
-- no blocks to skip: reads ~70 GB
SELECT ROUND(SUM(qty * prod_price), 2) AS ak_sales
FROM `roi-bq-demos.bq_demo_small.denorm`
WHERE cust_state = "AK"

-- clustered table query
-- same data clustered on cust_state; a bare filter on the cluster
-- column skips blocks: reads ~1.4 GB
SELECT ROUND(SUM(qty * prod_price), 2) AS ak_sales
FROM `roi-bq-demos.bq_demo_small.cl_by_state`
WHERE cust_state = "AK"

-- broken cluster filter query
-- wrapping the cluster column in a function turns off block
-- skipping: reads ~70 GB
SELECT ROUND(SUM(qty * prod_price), 2) AS ak_sales
FROM `roi-bq-demos.bq_demo_small.cl_by_state`
WHERE UPPER(cust_state) = "AK"
