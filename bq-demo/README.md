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

##Setup

### Notes
1. Setup takes about an hour to complete (largely background tasks)
2. This generate some significant charges for Dataflow processing, BigQuery storage, and demo query execution. Take that into account when deciding where/when to run it

### Instructions

1. Switch to the `bq-demo` directory of the gcp-demo repo.

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

5. Generate the data files for the normalized BQ tables. The amount of time this takes will depend on your quotas in the project where it's running - with 75 nodes, it takes about 30 minutes total. You will definitely need to run the Dataflow job in an environment where you have plenty of quota.

```python generate_data.py```

6. Load the data from the generated files in GCS into BigQuery. This will take on the order of 45 minutes to complete.

```
. ./load_data.sh
```

## Demo

1. Run the query found in norm_query.sql
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * 

2. Run the query found in denorm_query.sql
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Note you get the same results as with 1
    * This should be 50+% faster than #1

3. Run the first query found in nested_queries.sql
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Note you get the same results as with 1
    * This should be in same ballpark as #2

4. Run the second query found in nested_queries.sql
    * Note that amount of data processed
    * Note the structure of the query
    * Note the time taken to complete the query
    * Note you get the same results as with 1
    * This should be 60+% faster than 2&3

5. Run the third query found in nested_queries.sql
    * Note that amount of data processed
    * Note that this is processing all dates, not just august
    * Note the time taken to complete the query
    * You're going to compare this against clustered table




