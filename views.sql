-- subquery
SELECT
  *
FROM (
  SELECT
    cust_id,
    cust_name,
    cust_address,
    cust_zip
  FROM
    `roi-bq-demos.bq_demo.customer`
  WHERE
    cust_state="NJ")
WHERE
  cust_id <100000

-- with clause
WITH
  nj AS (
  SELECT
    cust_id,
    cust_name,
    cust_address,
    cust_zip
  FROM
    `roi-bq-demos.bq_demo.customer`
  WHERE
    cust_state="NJ")
SELECT
  *
FROM
  nj
WHERE
  cust_id<100000

-- create view
CREATE OR REPLACE VIEW
  `roi-bq-demos.bq_demo.nj_view` AS
SELECT
  cust_id,
  cust_name,
  cust_address,
  cust_zip
FROM
  `roi-bq-demos.bq_demo.customer`
WHERE
  cust_state="NJ"

-- query view
SELECT
  *
FROM
  roi-bq-demos.bq_demo.nj_view
WHERE
  cust_id < 100000