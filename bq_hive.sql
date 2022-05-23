-- query the external table
SELECT
  *
FROM
  class.ext_part

-- query external table with where clause
SELECT
  *
FROM
  class.ext_part
WHERE
  order_num="68610383-54"

--query external table on partition
SELECT
  *
FROM
  class.ext_part
WHERE
  order_date="2018-01-01"