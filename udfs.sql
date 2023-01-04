-- trim strings
SELECT
  text AS messy,
  TRIM(REGEXP_REPLACE(LOWER(text), '[^a-zA-Z0-9 ]+', '')) AS tidy
FROM
  `roi-bq-demos.bq_demo.messy_text`
  
-- create udf
CREATE OR REPLACE FUNCTION
  `class.tidy_string` (text STRING)
  RETURNS STRING AS TRIM(REGEXP_REPLACE(LOWER(text), '[^a-zA-Z0-9 ]+', ''));

-- query with SQL UDF
SELECT
  text AS messy,
  `class.tidy_string`(text) AS tidy
FROM
  `roi-bq-demos.bq_demo.messy_text`

-- create javascript udf
CREATE OR REPLACE FUNCTION
  `class.get_numbers`(str STRING)
  RETURNS NUMERIC
  LANGUAGE js AS '''
   return nlp(str).values(0).toNumber().out()
''' OPTIONS ( library="gs://fh-bigquery/js/compromise.min.11.14.0.js");

-- query with javascript udf
SELECT
  text,
  `class.get_numbers`(text) AS number
FROM
  `roi-bq-demos.bq_demo.number_strings`