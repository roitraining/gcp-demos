# make sure you have a dataset in current project name gcp_demos
# this creates the table used for demo
CREATE OR REPLACE TABLE
  gcp_demos.arrays AS
SELECT
  "row1" AS row_id,
  [1,
  2,
  3,
  4] AS some_numbers
UNION ALL
SELECT
  "row2" AS row_id,
  [2,
  4,
  8,
  16,
  32] AS some_numbers
UNION ALL
SELECT
  "row3" AS row_id,
  [5,
  10] AS some_numbers

  # show original row plus new column with sum of array
SELECT
  row_id,
  some_numbers,
  (
  SELECT
    SUM( n )
  FROM
    UNNEST(some_numbers) AS n ) AS sum
FROM
  `gcp_demos.arrays`

  # show original row plus new column with sum of array - 2nd approach
SELECT
  row_id,
  ARRAY_AGG(n) AS some_numbers,
  SUM(n) AS sum
FROM
  `gcp_demos.arrays`,
  UNNEST(some_numbers) AS n
GROUP BY
  row_id

# create a denormalized view
CREATE OR REPLACE VIEW
  gcp_demos.arrays_denorm_view AS
SELECT
  row_id,
  n
FROM
  gcp_demos.arrays,
  UNNEST(some_numbers) AS n

  # query the denormalized view
SELECT
  row_id,
  SUM(n),
  ARRAY_AGG(n) AS some_numbers
FROM
  gcp_demos.arrays_denorm_view
GROUP BY
  row_id