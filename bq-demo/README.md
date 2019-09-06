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

1. Open Cloud shell, and set gcloud to use a project where you want things billed.

2. Clone this repo to Cloud Shell

```
git clone https://github.com/roitraining/gcp-demos.git
```

3. Switch to the `bq-demo` directory.

4. In your project of choice, create a bucket to hold the data files

```
gsutil mb -c regional -l us-central1 gs://$DEVSHELL_PROJECT_ID-bq-demo
```

5. Generate the data files for the normalized BQ tables (the amount of time this takes will depend on your quotas in the project where it's running)

```python generate_data.py```