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
-- assumes dataset in current project named class
CREATE OR REPLACE VIEW
  `class.nj_view` AS
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
  `class.nj_view`
WHERE
  cust_id < 100000