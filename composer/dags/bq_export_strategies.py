# Purpose:
# Demonstrates multiple approaches to exporting BigQuery data to GCS in Airflow.
# Highlights that there are often many ways to accomplish tasks in Airflow.
#
# Preparation Needed:
# - Create an Airflow variable for your GCP project ID.
# - Ensure a GCS bucket exists with the same name as your project.
# - Install required dependencies in your Composer environment (BigQuery, GCS, pandas).

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.bigquery_to_gcs import (
    BigQueryToGCSOperator,
)
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from google.cloud import bigquery

import pandas as pd
import logging

# Default arguments for the DAG
default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
}


# Read GCP project and bucket from Airflow Variables
SOURCE_PROJECT_ID = "roi-bq-demos"
GCS_BUCKET = Variable.get("gcp_project_id")
DATASET_ID = "bq_demo"
TABLE_ID = "product"
OUTPUT_FILE = "product_export.json"

# DAG Definition
dag = DAG(
    "export_product_table_strategies",
    default_args=default_args,
    description="Export product table from BigQuery to GCS using multiple strategies",
    schedule_interval=None,
    catchup=False,
    tags=["bigquery", "gcs", "product", "multi-strategy"],
)


# 1. Export using BigQueryInsertJobOperator (EXPORT DATA)
export_with_insertjob = BigQueryInsertJobOperator(
    task_id="export_with_insertjob",
    configuration={
        "query": {
            "query": (
                f"""
                EXPORT DATA OPTIONS(
                    uri='gs://{GCS_BUCKET}/product/airflow_export_with_insertjob/*.json',
                    format='JSON'
                ) AS
                SELECT * FROM `{SOURCE_PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
                """
            ),
            "useLegacySql": False,
        }
    },
    location="US",
    dag=dag,
)

# 2. Export as Parquet using BigQueryToGCSOperator
export_with_parquet = BigQueryToGCSOperator(
    task_id="export_with_parquet",
    source_project_dataset_table=f"{SOURCE_PROJECT_ID}.{DATASET_ID}.{TABLE_ID}",
    destination_cloud_storage_uris=[
        f"gs://{GCS_BUCKET}/product/airflow_export_with_ToGCS.parquet"
    ],
    export_format="PARQUET",
    dag=dag,
)


def export_with_custom_logic(**context):
    client = bigquery.Client()

    # Query the table
    query = f"SELECT * FROM `{SOURCE_PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`"
    df = client.query(query).to_dataframe()

    # Custom processing
    # df_processed = df.apply(<custom_transformation>)
    df_processed = df

    # Export to various destinations
    df_processed.to_parquet(f"gs://{GCS_BUCKET}/product/airflow_export_custom.parquet")


# 3. Export as Parquet using BigQueryToGCSOperator
custom_export = PythonOperator(
    task_id="custom_export", python_callable=export_with_custom_logic, dag=dag
)
