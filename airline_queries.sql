# find all arrival entries for UA
SELECT
  date,
  arrival_state,
  arrival_delay
FROM
  `bigquery-samples.airline_ontime_data.flights`
WHERE
  airline_code="19977"

# find average delay by month by arrival_state
SELECT
  month,
  state,
  avg_delay,
  flights,
  early_flights,
  late_flights,
  ROUND(early_flights/flights*100,1) AS pct_early,
  ROUND(late_flights/flights*100,1) AS pct_late
FROM (
  SELECT
    SUBSTR(date,1,7) AS month,
    arrival_state AS state,
    ROUND(AVG(arrival_delay),1) AS avg_delay,
    COUNT(arrival_delay) AS flights,
    SUM(IF(arrival_delay<0.0,
        1,
        0)) AS early_flights,
    SUM(IF(arrival_delay>0.0,
        1,
        0)) AS late_flights
  FROM
    `bigquery-samples.airline_ontime_data.flights`
  WHERE
    airline_code="19977"
  GROUP BY
    month,
    state
  ORDER BY
    state,
    month DESC)