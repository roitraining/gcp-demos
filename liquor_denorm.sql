#standardSQL
SELECT
  county AS county,
  IF (gstore_total >0,
    ROUND(cstore_total/gstore_total * 100,1),
    0) AS cstore_percentage
FROM (
  SELECT
    county AS county,
    SUM(IF(cstore IS NULL,
        total,
        0)) AS gstore_total,
    SUM(IF(cstore IS NOT NULL,
        total,
        0)) AS cstore_total
  FROM
    `cpb200_liquor_sales.iowa_sales_denorm`
  GROUP BY
    county
  ORDER BY
    county)