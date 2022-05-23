-- view up-to-date table
SELECT *
FROM `roi-bq-demos.bq_demo.time_travel`

-- view table with only initial load
SELECT *
FROM `roi-bq-demos.bq_demo.time_travel`
  FOR SYSTEM_TIME AS OF timestamp("2022-05-20 18:25:23+00");

-- create restoration table
CREATE OR REPLACE TABLE
  class.time_travel_restore AS (
  SELECT
    *
  FROM
    `roi-bq-demos.bq_demo.time_travel` FOR SYSTEM_TIME AS OF TIMESTAMP("2022-05-20 18:25:23+00"));