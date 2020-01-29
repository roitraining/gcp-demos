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

### Notes

There are two ways to do setup.
- Start with a pre-created normalized data set
- Start by creating your own normalized data set

The former approach uses this normalized data set:

```
roi-bq-demo.bq_demo
```

which has the following tables:
- customer: 75M rows
- product: 10K rows
- order: 7.5B rows
- line_item: 75B rows

This is the largest dataset we can reasonably store for instructor use. If you want a larger dataset, you can follow the instructions for creating your own normalized tables.

### Setup - general

1. Log into the cloud console, and select an appropriate project. Queries used to derive the not-normalized tables and do the demos are expensive, so choose your project wisely (i.e. do not use a project billable to ROI Training even if you can).

2. In your target project, make sure that there is a dataset named `bq_demo` (create it if necessary).

### Setup - standard normalized tables

1. Run the query in __load_data.sql__. This will take about 70 minutes, cost $150, and create four new tables in your target project/dataset:
- denorm
- nested_once
- table_nested_partitioned
- table_nested_partitioned_clustered

### Setup - create your own normalized tables

1. Open Cloud Shell

2. In your project of choice, create a bucket to hold the data files

```
gsutil mb -c regional -l us-central1 gs://$DEVSHELL_PROJECT_ID
```


3. Create and activate a virtual environment

```
virtualenv ~/venvs/bq-demo
source ~/venvs/bq-demo/bin/activate
```

4. Install the required Python packages

```
pip install -r requirements.txt
```

5. Generate the data files for the normalized BQ tables. The amount of time this takes will depend on your quotas in the project where it's running - with 100 16cpu nodes, it takes about 70 minutes total and costs $xx. You will definitely need to run the Dataflow job in an environment where you have plenty of quota. Make sure to replace the placeholders in the command-line below:

```
python generate_data.py \
    --project=<project-id> \
    --bucket=<bucket-name> \
    --save_main_session \
    --runner=DataflowRunner \
    --worker_machine_type=<machine-type> \
    --region=<region> \
    --customers=<# customers> \
    --products=10000 \
    --orders=<#orders> \
```

6. Load the data from the generated files in GCS into BigQuery. This will take on the order of 75 minutes to complete, and cost about $150.

```
. ./load_data.sh
```

When prompted, enter the project name where the data will reside, and the bucket where Dataflow stored the import files.

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


