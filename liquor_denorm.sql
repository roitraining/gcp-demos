#standardSQL
SELECT
  gstore.county AS county,
  ROUND(cstore_total/gstore_total * 100,1) AS cstore_percentage
FROM (
  SELECT 
    county,  
    sum(total) AS gstore_total 
  FROM 
    `cpb200_liquor_sales.iowa_sales_denorm`
  WHERE cstore is null
  GROUP BY 
    county
ORDER BY county