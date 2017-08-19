# uses standard sql
# medicare claims in 2014
SELECT
 nppes_provider_state AS state,
 ROUND(SUM(total_claim_count) / 1e6) AS total_claim_count_millions
FROM
 `bigquery-public-data.medicare.part_d_prescriber_2014`
GROUP BY
 state
ORDER BY
 total_claim_count_millions DESC
LIMIT 5;

# query syntax
SELECT
 airline,
 SUM(IF(arrival_delay > 0, 1, 0)) AS num_delayed,
 COUNT(arrival_delay) AS total_flights
FROM
 `bigquery-samples.airline_ontime_data.flights`
WHERE
 arrival_airport='OKC'
 AND departure_airport='DFW'
GROUP BY
 airline;

# aggregate
SELECT
 airline,
 departure_airport,
 SUM(IF(arrival_delay > 0, 1, 0)) AS num_delayed,
 COUNT(arrival_delay) AS total_flights
FROM
 `bigquery-samples.airline_ontime_data.flights`
WHERE
 arrival_airport='OKC'
GROUP BY
 airline, departure_airport;

 # subqueries
 SELECT
 airline, departure_airport, num_delayed,
 total_flights, num_delayed/total_flights AS delayed_frac
FROM
# Nested Query
(SELECT
 airline, departure_airport,
 SUM(IF(arrival_delay > 0, 1, 0)) AS num_delayed,
 COUNT(arrival_delay) AS total_flights
FROM
 `bigquery-samples.airline_ontime_data.flights`
WHERE
 arrival_airport='OKC'
GROUP BY
 airline, departure_airport)
WHERE total_flights > 5
ORDER BY dela

# union all 
SELECT
 # Find the average temperature
 ROUND(AVG(temp),2) AS temp_avg_f,
 stn AS noaa_station_number
FROM
 (
 SELECT * FROM `bigquery-public-data.noaa_gsod.gsod2015` UNION ALL
 SELECT * FROM `bigquery-public-data.noaa_gsod.gsod2016` UNION ALL
 SELECT * FROM `bigquery-public-data.noaa_gsod.gsod2017`
 )
GROUP BY 2
ORDER BY 1 DESC
LIMIT 5;

# wildcards
# Find the 5 hottest NOAA stations since 2015
SELECT
 # Find the average temperature
 ROUND(AVG(temp),2) AS temp_avg_f,
 stn AS noaa_station_number
FROM
 `bigquery-public-data.noaa_gsod.gsod*`
WHERE
 _TABLE_SUFFIX >= '2015'
GROUP BY 2
ORDER BY 1 DESC
LIMIT 5;

# joins
SELECT
 f.airline,
 SUM(IF(f.arrival_delay > 0, 1, 0)) AS num_delayed,
 COUNT(f.arrival_delay) AS total_flights
FROM
 `bigquery-samples.airline_ontime_data.flights` AS f
JOIN (
 SELECT
 # Convert date fields to YYYY-MM-DD
 CONCAT(CAST(year AS STRING), '-', LPAD(CAST(month AS STRING),2,'0'), '-',
LPAD(CAST(day AS STRING),2,'0')) AS rainyday
 FROM
 `bigquery-samples.weather_geo.gsod`
 WHERE
 station_number = 725030
 # Only return days it rained
 AND total_precipitation > 0) AS w
ON
 w.rainyday = f.date
WHERE f.arrival_airport 


# count distinct
WITH
  WashingtonStations AS (
  SELECT
    weather.stn AS station_id,
    ANY_VALUE(station.name) AS name
  FROM
    `bigquery-public-data.noaa_gsod.stations` AS station
  INNER JOIN
    `bigquery-public-data.noaa_gsod.gsod2015` AS weather
  ON
    station.usaf = weather.stn
  WHERE
    station.state = 'WA'
    AND station.usaf != '999999'
  GROUP BY
    station_id )
SELECT
  washington_stations.name,
  (
  SELECT
    COUNT(DISTINCT CONCAT(year, mo, da))
  FROM
    `bigquery-public-data.noaa_gsod.gsod2015` AS weather
  WHERE
    washington_stations.station_id = weather.stn
    AND prcp > 0
    AND prcp < 99) AS rainy_days
FROM
  WashingtonStations AS washington_stations
ORDER BY
  rainy_days DESC;

# alt to above
SELECT
  wa.station_name AS station_name,
  weather.rainy_days AS rainy_days
FROM (
  SELECT
    usaf AS station_id,
    name AS station_name
  FROM
    `bigquery-public-data.noaa_gsod.stations`
  WHERE
    state = 'WA'
    AND usaf != '999999') AS wa
JOIN (
  SELECT
    stn AS station_id,
    COUNT(*) AS rainy_days
  FROM
    `bigquery-public-data.noaa_gsod.gsod2015`
  WHERE
    prcp > 0
    AND prcp < 99
  GROUP BY
    station_id) AS weather
ON
  weather.station_id = wa.station_id
ORDER BY
  rainy_days DESC;

# array/struct
  # Top two Hacker News articles by day
WITH
  TitlesAndScores AS (
  SELECT
    ARRAY_AGG(STRUCT(title,
        score)) AS titles,
    EXTRACT(DATE
    FROM
      time_ts) AS date
  FROM
    `bigquery-public-data.hacker_news.stories`
  WHERE
    score IS NOT NULL
    AND title IS NOT NULL
  GROUP BY
    date)
SELECT
  date,
  ARRAY(
  SELECT
    AS STRUCT title,
    score
  FROM
    UNNEST(titles)
  ORDER BY
    score DESC
  LIMIT
    2) AS top_articles
FROM
  TitlesAndScores;

# alt to above
SELECT
  day,
  ARRAY_AGG(top_articles) AS top_articles
FROM (
  SELECT
    DATE(time_ts) AS day,
    ROW_NUMBER() OVER (PARTITION BY DATE(time_ts)
    ORDER BY
      score DESC) AS row,
    STRUCT (title,
      score) AS top_articles
  FROM
    `bigquery-public-data.hacker_news.stories`
  WHERE
    score IS NOT NULL
    AND title IS NOT NULL)
WHERE
  row <=2
GROUP BY
  day
ORDER BY
  day DESC

# join condition
# Top name frequency in Shakespeare
  # Top name frequency in Shakespeare
WITH
  TopNames AS (
  SELECT
    name,
    SUM(number) AS occurrences
  FROM
    `bigquery-public-data.usa_names.usa_1910_2013`
  GROUP BY
    name
  ORDER BY
    occurrences DESC
  LIMIT
    100)
SELECT
  name,
  SUM(word_count) AS frequency
FROM
  TopNames
JOIN
  `bigquery-public-data.samples.shakespeare`
ON
  STARTS_WITH(word, name)
GROUP BY
  name
ORDER BY
  frequency DESC
LIMIT
  10;

# regex
SELECT
  word,
  COUNT(word) AS count
FROM
  `publicdata.samples.shakespeare`
WHERE
  ( REGEXP_CONTAINS(word,r'^\w\w\'\w\w') )
GROUP BY
  word
ORDER BY
  count

# window
SELECT
  corpus,
  word,
  word_count,
  RANK() OVER (PARTITION BY corpus ORDER BY word_count DESC) AS rank
FROM
  `publicdata.samples.shakespeare`
WHERE
  LENGTH(word) > 10
  AND word_count > 10
LIMIT
  40;

#SQL udf
CREATE TEMPORARY FUNCTION
  addFourAndDivide(x INT64,
    y INT64) AS ((x + 4) / y);
WITH
  numbers AS (
  SELECT
    1 AS val
  UNION ALL
  SELECT
    3 AS val
  UNION ALL
  SELECT
    4 AS val
  UNION ALL
  SELECT
    5 AS val)
SELECT
  val,
  addFourAndDivide(val,
    2) AS result
FROM
  numbers;

#javascript udf
CREATE TEMPORARY FUNCTION
  multiplyInputs(x FLOAT64,
    y FLOAT64)
  RETURNS FLOAT64
  LANGUAGE js AS """
 return x*y;
""";
WITH
  numbers AS (
  SELECT
    1 AS x,
    5 AS y
  UNION ALL
  SELECT
    2 AS x,
    10 AS y
  UNION ALL
  SELECT
    3 AS x,
    15 AS y)
SELECT
  x,
  y,
  multiplyInputs(x,
    y) AS product
FROM
  numbers;