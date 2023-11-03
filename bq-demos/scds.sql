-- # dml to update array, match element in array, update element in array

-- take 1
-- rebuild the entire table
-- takes about 18 minutes
CREATE OR REPLACE TABLE
  `bq_demo.nested_once` AS (
  WITH

    -- denormalize the nested table
    denorm AS (
    SELECT
      * EXCEPT (line_items)
    FROM
      `bq_demo.nested_once` n,
      n.line_items ),

    -- update line_items with new price if there's an entry in price_updates
    updated AS (
    SELECT
      denorm.* EXCEPT(prod_price),
      if(pu.prod_price is not null, pu.prod_price, denorm.prod_price) AS prod_price
    FROM
      denorm
    left JOIN
      `bq_demo.price_updates` pu
    ON
      denorm.prod_code = pu.prod_code)

  -- reconstitute the nested table
  SELECT
    * EXCEPT (line_item_num,
      prod_code,
      qty,
      prod_name,
      prod_desc,
      prod_price),
    ARRAY_AGG(STRUCT(line_item_num,
        prod_code,
        qty,
        prod_name,
        prod_desc,
        prod_price)) as line_items
  FROM
    updated
  GROUP BY
    order_num,
    order_date,
    cust_phone,
    cust_email,
    cust_zip,
    cust_state,
    cust_address,
    cust_name,
    cust_id)

-- take 2
-- stored procedure to update nested once
-- uses temporary table, updates only rows that need to be updated
-- takes about 19 minutes
BEGIN
  -- generate the update table that has only updated order rows
  CREATE TEMPORARY TABLE m AS (
  WITH
    -- denormalize the nested table
    denorm AS (
    SELECT
      * EXCEPT(line_items)
    FROM
      `bq_demo.nested_once` o,
      UNNEST(line_items) l),

    -- get the order numbers that have rows that need to be updated
    order_numbers AS (
    SELECT
      order_num
    FROM
      denorm d
    JOIN
      `bq_demo.price_updates` p
    ON
      d.prod_code = p.prod_code
    GROUP BY
      order_num),

    -- get the rows that need to be updated
    relevant AS (
    SELECT
      d.*
    FROM
      denorm d
    JOIN
      order_numbers o
    ON
      o.order_num = d.order_num ),

    -- update line_items with new price if there's an entry in price_updates
    updated AS (
    SELECT
      r.* EXCEPT (prod_price),
      IFNULL(p.prod_price,r.prod_price) AS prod_price
    FROM
      relevant r
    LEFT JOIN
      `bq_demo.price_updates` p
    ON
      r.prod_code = p.prod_code)

  -- reconstitute the nested table
  SELECT
    * EXCEPT (line_item_num,
      prod_code,
      qty,
      prod_name,
      prod_desc,
      prod_price),
    ARRAY_AGG(STRUCT(line_item_num,
        prod_code,
        qty,
        prod_name,
        prod_desc,
        prod_price)) AS line_items
  FROM
    updated
  GROUP BY
    order_num,
    order_date,
    cust_phone,
    cust_email,
    cust_zip,
    cust_state,
    cust_address,
    cust_name,
    cust_id);

-- merge the updated order rows into the original table
MERGE
  `bq_demo.nested_once` n
USING
  m
ON
  m.order_num = n.order_num
  WHEN MATCHED THEN UPDATE SET line_items = m.line_items;
END

-- take 3 
-- stored procedure to update nested once
-- does order search before denormalizing
-- avoids temporary table
-- takes like 12-13 minutes
BEGIN
-- create an array of price_updates
-- we can use this to filter rows that need to be updated
-- and avoid the join
DECLARE
  prod_codes DEFAULT (array(
  SELECT
    prod_code
  FROM
    bq_demo.price_updates));

-- avoid the temp table, put everything into the merge
MERGE
  bq_demo.nested_once n
USING
  (
  WITH

    -- get the rows that need to be updated
    relevant AS (
    SELECT
      *
    FROM
      bq_demo.nested_once
    WHERE
      EXISTS (
      SELECT
        *
      FROM
        UNNEST(line_items) as li
      WHERE
        prod_code IN unnest(prod_codes))),

    -- denormalize the rows that need to be updated
    denorm AS (
    SELECT
      * EXCEPT (line_items)
    FROM
      relevant,
      relevant.line_items),

    -- update line_items with new price if there's an entry in price_updates
    updated AS (
    SELECT
      d.* EXCEPT (prod_price),
      IFNULL(p.prod_price,d.prod_price) AS prod_price
    FROM
      denorm d
    LEFT JOIN
      `bq_demo.price_updates` p
    ON
      d.prod_code = p.prod_code)

  -- reconstitute the nested table
  SELECT
    * EXCEPT (line_item_num,
      prod_code,
      qty,
      prod_name,
      prod_desc,
      prod_price),
    ARRAY_AGG(STRUCT(line_item_num,
        prod_code,
        qty,
        prod_name,
        prod_desc,
        prod_price)) AS line_items
  FROM
    updated
  GROUP BY
    order_num,
    order_date,
    cust_phone,
    cust_email,
    cust_zip,
    cust_state,
    cust_address,
    cust_name,
    cust_id) u
ON
  u.order_num = n.order_num
  -- replace array with new array with update values
  WHEN MATCHED THEN UPDATE SET line_items = u.line_items;
END

--take 4
-- stored procedure to update nested once
-- filters before denormalizing
-- uses merge to update denorm
-- uses merge to reconstitute rows then merge into source
-- takes 12-13 minutes (12.5 with 5K slots)
BEGIN

-- create an array of price_updates
DECLARE
  prod_codes DEFAULT (ARRAY(
    SELECT
      prod_code
    FROM
      bq_demo.price_updates)); 
-- find the rows that need to be updated
-- denormalize them
CREATE TEMPORARY TABLE denorm AS (
  WITH
    rows_to_update AS (
    SELECT
      *
    FROM
      bq_demo.nested_once
    WHERE
      EXISTS (
      SELECT
        *
      FROM
        UNNEST(line_items) AS li
      WHERE
        prod_code IN UNNEST(prod_codes)))
  SELECT
    * EXCEPT (line_items)
  FROM
    rows_to_update,
    rows_to_update.line_items);
-- update the denormalized rows
MERGE
  denorm d
USING
  bq_demo.price_updates p
ON
  d.prod_code = p.prod_code
WHEN MATCHED THEN 
UPDATE 
SET prod_price = p.prd_price; 

-- merge
-- create nested rows, then replace the old rows
MERGE bq_demo.nested_once n 
USING (
SELECT * EXCEPT (line_item_num, prod_code, qty, prod_name, prod_desc, prod_price), ARRAY_AGG(STRUCT(line_item_num, prod_code, qty, prod_name, prod_desc, prod_price)) AS line_items FROM denorm d GROUP BY order_num, order_date, cust_phone, cust_email, cust_zip, cust_state, cust_address, cust_name, cust_id) u 
ON u.order_num = n.order_num
WHEN MATCHED THEN
UPDATE
SET
  line_items = u.line_items;
END

-- To dos
-- # dml for type 1 dimension
-- # dml for type 2 dimension
-- # dml to update array, match col
-- # dml to update array, match element in array, delete element in array
-- # dml to update array, match element in array, update elements in array
-- # dml to update array, match element in array, delete elements in array
-- # dml to update array, match element in array, insert element into array
-- # dml to update array, match element in array, insert elements into array