WITH
  totals AS (
  SELECT
    cy.county AS county,
    SUM(IF(c.store IS NULL,
        total,
        0)) AS gstore_total,
    SUM(IF(c.store IS NOT NULL,
        total,
        0)) AS cstore_total
  FROM
    `cpb200_liquor_sales.sales` AS s
  JOIN
    `cpb200_liquor_sales.store` AS st
  ON
    s.store = st.store
  JOIN
    `cpb200_liquor_sales.county` AS cy
  ON
    st.county_number = cy.county_number
  LEFT OUTER JOIN
    `cpb200_liquor_sales.convenience_store` AS c
  ON
    s.store = c.store
  GROUP BY
    county )
SELECT
  county,
  IF(gstore_total <> 0,
    ROUND(cstore_total/gstore_total*100,2),
    0)
FROM
  totals
ORDER BY
  county