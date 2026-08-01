-- =====================================================================
-- BigQuery Iceberg tutorial: all SQL, in tutorial order.
--
-- The placeholders below are filled in for you by iceberg_sql.sh, which
-- reads the project and bucket from your environment:
--
--   ./iceberg_sql.sh --list                        list statement names
--   ./iceberg_sql.sh 'create managed table query'  one statement
--   ./iceberg_sql.sh                               this whole file
--
-- See ICEBERG_TUTORIAL.md for the two variables to export first.
-- =====================================================================


-- ---------------------------------------------------------------------
-- PART 1: MANAGED ICEBERG TABLES
-- BigQuery owns the metadata and writes the data. Full DML. Data lands
-- in your bucket as open Parquet + Iceberg metadata.
-- ---------------------------------------------------------------------

-- create managed table query
CREATE OR REPLACE TABLE `PROJECT_ID.iceberg_lab.orders_managed` (
  order_id INT64,
  customer STRING,
  amount NUMERIC,
  order_date DATE
)
WITH CONNECTION `PROJECT_ID.us.big_lake_demo`
OPTIONS (
  file_format = 'PARQUET',
  table_format = 'ICEBERG',
  storage_uri = 'gs://BUCKET/iceberg_lab/orders_managed'
);

-- insert query
INSERT INTO `PROJECT_ID.iceberg_lab.orders_managed` VALUES
  (1, 'acme',     100.00, DATE '2026-01-15'),
  (2, 'globex',   250.50, DATE '2026-01-16'),
  (3, 'initech',   75.25, DATE '2026-01-17');

-- update query
-- proves this is a read-write table, unlike an external table
UPDATE `PROJECT_ID.iceberg_lab.orders_managed`
SET amount = 150.00
WHERE order_id = 1;

-- delete query
DELETE FROM `PROJECT_ID.iceberg_lab.orders_managed`
WHERE order_id = 3;

-- verify query
SELECT * FROM `PROJECT_ID.iceberg_lab.orders_managed` ORDER BY order_id;

-- export metadata query
-- REQUIRED before any external engine can read this table. Until you run
-- this, the bucket holds only a stub v0.metadata.json that points back at
-- BigQuery, and Spark fails with "Cannot parse missing int: format-version".
EXPORT TABLE METADATA FROM `PROJECT_ID.iceberg_lab.orders_managed`;


-- ---------------------------------------------------------------------
-- PART 2: LAKEHOUSE RUNTIME CATALOG TABLES
-- Metadata lives in the Lakehouse runtime catalog and is served over the
-- Iceberg REST catalog endpoint, so BigQuery and Spark/Trino/Flink share
-- one catalog. Uses four-part names: project.catalog.namespace.table
-- ---------------------------------------------------------------------

-- create catalog table query
-- NOTE: see the tutorial's "Known gap" section. This did not resolve from
-- the bq CLI during authoring; try it in the BigQuery console.
CREATE TABLE `PROJECT_ID.iceberg_demo.sales.orders` (
  id INT64,
  data STRING
);

-- insert into catalog table query
INSERT INTO `PROJECT_ID.iceberg_demo.sales.orders` VALUES
  (1, 'alpha'),
  (2, 'beta');

-- query catalog table query
SELECT * FROM `PROJECT_ID.iceberg_demo.sales.orders` ORDER BY id;


-- ---------------------------------------------------------------------
-- PART 3: EXTERNAL ICEBERG TABLES
-- Someone else owns the data and metadata. BigQuery reads only, and reads
-- one pinned snapshot.
-- ---------------------------------------------------------------------

-- create external table query
-- The uris value points at ONE metadata JSON file, which is a single
-- snapshot. Get the current filename from the bucket:
--   gcloud storage ls gs://BUCKET/iceberg_lab/orders_managed/metadata/
CREATE OR REPLACE EXTERNAL TABLE `PROJECT_ID.iceberg_lab.orders_external`
WITH CONNECTION `PROJECT_ID.us.big_lake_demo`
OPTIONS (
  format = 'ICEBERG',
  uris = ['gs://BUCKET/iceberg_lab/orders_managed/metadata/vNNNNNNNNNN.metadata.json']
);

-- query external table query
SELECT * FROM `PROJECT_ID.iceberg_lab.orders_external` ORDER BY order_id;

-- external tables are read only query
-- fails with: "DML statements are only supported over tables that have
-- data stored in BigQuery"
INSERT INTO `PROJECT_ID.iceberg_lab.orders_external`
VALUES (99, 'nope', 0.00, CURRENT_DATE());

-- prove the snapshot is pinned query
-- 1. add a row to the managed table
INSERT INTO `PROJECT_ID.iceberg_lab.orders_managed`
VALUES (4, 'umbrella', 500.00, DATE '2026-01-18');

-- 2. compare the two counts: the managed table sees the new row, the
--    external table does not, because it still points at the old
--    metadata file. Re-run EXPORT TABLE METADATA and recreate the
--    external table to catch up.
SELECT 'managed'  AS which, COUNT(*) AS n
FROM `PROJECT_ID.iceberg_lab.orders_managed`
UNION ALL
SELECT 'external' AS which, COUNT(*) AS n
FROM `PROJECT_ID.iceberg_lab.orders_external`;


-- ---------------------------------------------------------------------
-- CLEANUP
--
-- These statements remove the TABLES only. They do not remove the dataset,
-- the namespace, or the catalog. For a full teardown run:
--   ./iceberg_teardown.sh PROJECT_ID BUCKET
-- ---------------------------------------------------------------------

-- cleanup query
DROP TABLE IF EXISTS `PROJECT_ID.iceberg_lab.orders_managed`;
DROP EXTERNAL TABLE IF EXISTS `PROJECT_ID.iceberg_lab.orders_external`;
DROP TABLE IF EXISTS `PROJECT_ID.iceberg_demo.sales.orders`;
