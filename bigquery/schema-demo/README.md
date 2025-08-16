# ROI BigQuery Schema performance demo

## Goal
The goal of this demo is to show the relative performance of different schema choices in BigQuery.

After setup, there will be tables with the same data stored in tables with varying schemas:

- Normalized w/multiple tables
- Fully denormalized
- Single-level nesting (one row per order)
- Single-level nesting with partitioning
- Single-level nesting with partitioning and clustering

You can demo the changes in query performance and cost with these different schema.

Incidentally, this also provides the potential to demo Dataflow, BigQuery load techniques, doing intra-BigQuery ETL, etc.

## Setup

This demo uses this normalized data set: **roi-bq-demos.bq_demo** which has the following tables:
- customer: 75M rows
- product: 10K rows
- order: 7.5B rows
- line_item: 75B rows
- order_part: 7.5B rows (partitioned on `order_date`)


This is the largest dataset we can reasonably store for instructor use. If you want a larger dataset, you can create your own - the pieces you need are found in this directory.

1. Log into the cloud console, and select an appropriate project. Queries used to derive the not-normalized tables and do the demos are expensive, so choose your project wisely.

2. In your target project, make sure that there is a dataset named `bq_demo` (create it if necessary).

3. Run the query in **load_data.sql**. This will take about 70 minutes, cost $200, and create four new tables in your target project/dataset:
- denorm
- nested_once
- table_nested_partitioned
- table_nested_partitioned_clustered

## Demo

Load the BQ user interface in the project where you have the dataset.

1. Run the `base normalized tables` query found in **norm_query.sql**
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Example run: 2TB, 140 seconds, $12.50

2. Run the `normalized tables with order_part table` query found in **norm_query.sql**
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Example run: 1.8TB, 125 seconds, $10=1.25
    * Note that partitioning did reduce the data read, and the time taken, but the win was minimal given the size of the line_item table -> this is the gating factor. You can show the execution graph to drive this hom.

3. Run the query found in **denorm_query.sql**
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Note you get the same results as with 1
    * Example run: 2.2TB, 24 seconds, $13.75

3. Run the first query found in **nested_queries.sql**
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Note you get the same results as with 1
    * Example run: 1.2TB, 6.4 seconds, $7.50
  
4. Run the second query found in **nested_queries.sql**
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Note you get the same results as with 1
    * Example run: xTB, x seconds, $x

5. Run queries 3-4-5 from **nested_queries.sql**
    * Note the amount of data processed for each
    * Note the query time for each
    * You should seeing decreases for each one
    * Example runs
        * 1.2TB, 6.3 seconds, $7
        * 614G, 3.8 seconds, $3
        * 11GB, 3.2 seconds, $.06