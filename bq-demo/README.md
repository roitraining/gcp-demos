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
- Two-level nesting (one row per customer)

You can demo the changes in query curation and cost with these different schema.

Incidentally, this also provides the potential to demo Dataflow, BigQuery load techniques, doing intra-BigQuery ETL, etc.

## Setup

### Notes
1. Setup takes about an hour to complete (largely background tasks)

2. This generates some significant charges for Dataflow processing, BigQuery storage, and demo query execution. Take that into account when deciding where/when to run it

### Instructions

1. Switch to the __bq-demo__ directory of the __gcp-demo__ repo.

2. In your project of choice, create a bucket to hold the data files

```
gsutil mb -c regional -l us-central1 gs://$DEVSHELL_PROJECT_ID-bq-demo
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

5. In your target project, make sure that there is a dataset named `bq_demo` (create it if necessary).

6. Generate the data files for the normalized BQ tables. The amount of time this takes will depend on your quotas in the project where it's running - with 75 nodes, it takes about 30 minutes total. You will definitely need to run the Dataflow job in an environment where you have plenty of quota.

```python generate_data.py```

7. Load the data from the generated files in GCS into BigQuery. This will take on the order of 45 minutes to complete.

```
. ./load_data.sh
```

## Demo

Load the BQ user interface in the project where you have the dataset. The queries are written with the project name in the table reference, so if you run the queries in another project you'll need to add the project name at every appropriate line in the query.

1. Run the query found in __norm_query.sql__
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query

2. Run the query found in __denorm_query.sql__
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Note you get the same results as with 1
    * This should be 50+% faster than #1

3. Run the first query found in __nested_queries.sql__
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Note you get the same results as with 1
    * This should be in same ballpark as #2

4. Run the second query found in __nested_queries.sql__
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Note you get the same results as with 1
    * This should be 60+% faster than 2&3

There are some additional demos you can do.


* You can run the 3rd and 4th queries within the __nested_queries.sql__ file. The goal of these queries to show performance deltas between partitioned and partitioned/clustered tables. The problem is, I'm not seeing the kind of differences you would expect, so this demo may not be interesting.

* You can run the 5th query in the __nested_queries.sql__ file to show performance, cost, and query mechanics when querying a table with multiple levels of nesting.

* If you don't want to have to build the big dataset for these demos, you can run the same queries against a small dataset that already exists. Open BigQuery pointing to the __roi-bq-demo__ project in the __roicgp__ organization and run the queries there.