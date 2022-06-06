-- view up-to-date table
SELECT
  month,
  COUNT(*)
FROM
  `class.time_travel`
GROUP BY
  month;

-- view table with only initial load
SELECT
  month,
  COUNT(*)
FROM
  `class.time_travel` FOR SYSTEM_TIME AS OF TIMESTAMP_SECONDS(target)
GROUP BY
  month;

-- create restoration table
CREATE OR REPLACE TABLE
  class.time_travel_restore AS (
  SELECT
    *
  FROM
    `class.time_travel` FOR SYSTEM_TIME AS OF TIMESTAMP_SECONDS(target))
