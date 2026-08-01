-- join before declaring anything query
-- the customer table is joined only to satisfy the join; no customer
-- column is selected, so the join cannot change the answer
SELECT
  o.order_num,
  o.order_date
FROM
  `roi-bq-demos.bq_demo_small.order` o
JOIN
  `roi-bq-demos.bq_demo_small.customer` c
USING
  (cust_id)
WHERE
  o.order_date = DATE '2018-06-15'

-- declare the primary key query
-- metadata only: NOT ENFORCED means BigQuery never checks it, and
-- ADD PRIMARY KEY rewrites no data
ALTER TABLE `your_project.class.customer`
  ADD PRIMARY KEY (cust_id) NOT ENFORCED

-- declare the foreign key query
-- tells the optimizer every order row matches exactly one customer row
ALTER TABLE `your_project.class.order`
  ADD FOREIGN KEY (cust_id)
  REFERENCES `your_project.class.customer` (cust_id)
  NOT ENFORCED

-- check what you declared query
-- constraints show up in the table's metadata, not in the data
SELECT
  constraint_name,
  table_name,
  constraint_type
FROM
  `your_project.class.INFORMATION_SCHEMA.TABLE_CONSTRAINTS`
ORDER BY
  table_name

-- build a table pair that breaks the promise query
-- emp 3 belongs to dept 99, which does not exist: the foreign key
-- declared below is a lie
CREATE OR REPLACE TABLE class.dept (
  dept_id INT64,
  dept_name STRING,
  PRIMARY KEY (dept_id) NOT ENFORCED
) AS
SELECT 1, 'Sales'
UNION ALL
SELECT 2, 'Support';

CREATE OR REPLACE TABLE class.emp (
  emp_id INT64,
  dept_id INT64
) AS
SELECT 1, 1
UNION ALL
SELECT 2, 2
UNION ALL
SELECT 3, 99

-- the honest answer query
-- run this before declaring the foreign key: emp 3 has no department,
-- so an inner join drops it
SELECT
  e.emp_id
FROM
  class.emp e
JOIN
  class.dept d
USING
  (dept_id)
ORDER BY
  emp_id

-- declare the false foreign key query
-- nothing is validated, so this succeeds even though it is untrue
ALTER TABLE class.emp
  ADD FOREIGN KEY (dept_id)
  REFERENCES class.dept (dept_id)
  NOT ENFORCED
