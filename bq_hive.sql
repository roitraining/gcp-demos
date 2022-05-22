-- CREATE A PERMANENT EXTERNAL TABLE (console)
-- 1. select your dataset 
-- 2. from three-dot menu, select create table
-- 3. in Create table from, select Google Cloud Storage
-- 4. in Select file... enter jwd-gcp-demos/orders_partitioned/*
-- 5. in File format select parquet
-- 6. select Source data partitioning
-- 7. in Select Source... enter gs://jwd-gcp-demos/orders_partitioned/
-- 8. in Table, enter ext_part 
-- 9. in Table type select External table
-- 10. in Schema, select Auto detect
-- 11. Click CREATE TABLE

-- query the external table
SELECT
  *
FROM
  class.ext_part

-- query external table with where clause
SELECT
  *
FROM
  class.ext_part
WHERE
  order_num="68610383-54"

--query external table on partition
SELECT
  *
FROM
  class.ext_part
WHERE
  order_date="2018-01-01"