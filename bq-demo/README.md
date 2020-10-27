# ROI GCP Training Demos

## Goal
The goal of this demo is to show relative performance
of different schema choices in BigQuery.

After setup, there will be tables with the same data stored in tables with varying schemas:

- Normalized w/multiple tables
- Fully denormalized
- Single-level nesting (one row per order)
- Single-level nesting with partitioning
- Single-level nesting with partitioning and clustering

You can demo the changes in query performance and cost with these different schema.

Incidentally, this also provides the potential to demo Dataflow, BigQuery load techniques, doing intra-BigQuery ETL, etc.

## Setup

This demo uses this normalized data set:

```
roi-bq-demo.bq_demo
```

which has the following tables:
- customer: 75M rows
- product: 10K rows
- order: 7.5B rows
- line_item: 75B rows

This is the largest dataset we can reasonably store for instructor use.
If you want a larger dataset, you can create your own - the pieces you need
are found in this directory.

1. Log into the cloud console, and select an appropriate project. Queries used to derive the not-normalized tables and do the demos are expensive, so choose your project wisely (i.e. do not use a project billable to ROI Training even if you can). For recommended strategy, visit the demos Slack channel.

2. In your target project, make sure that there is a dataset named `bq_demo` (create it if necessary).

3. Run the query in __load_data.sql__. This will take about 70 minutes, cost $150, and create four new tables in your target project/dataset:
- denorm
- nested_once
- table_nested_partitioned
- table_nested_partitioned_clustered

## Demo

Load the BQ user interface in the project where you have the dataset. The queries are written with the project name in the table reference, so if you run the queries in another project you'll need to add the project name at every appropriate line in the query.

1. Run the query found in __norm_query.sql__
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Example run: 2TB, 110 seconds, $10

2. Run the query found in __denorm_query.sql__
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Note you get the same results as with 1
    * Example run: 2.2TB, 24 seconds, $11

3. Run the first query found in __nested_queries.sql__
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Note you get the same results as with 1
    * Example run: 1.2TB, 6.4 seconds, $7

4. Run the second query found in __nested_queries.sql__
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Note you get the same results as with 1
    * Example run: 0.1TB, 6.0 seconds, $0.50

5. Run queries 3-4-5 from __nested_queries.sql__
    * Note the amount of data processed for each
    * Note the query time for each
    * You should seeing decreases for each one
    * Example runs
        * 1.2TB, 6.3 seconds, $7
        * 614G, 3.8 seconds, $3
        * 11GB, 3.2 seconds, $.06