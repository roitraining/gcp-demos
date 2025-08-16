# Example Scenario:
# A marketing analyst wants to identify the top customers for the week of Christmas.
# This DAG exports top customers from BigQuery to a GCS bucket to be fed to a marketing campaign.
#
# Prerequisites:
# 1. Create an Airflow variable for your project: gcp_project_id
# 2. Create a 'marketing' dataset in BigQuery.
# 3. Ensure a GCS bucket exists with the project name.
#
# Demo Instructions:
# 1. Place this DAG in your Airflow DAGs folder.
# 2. Trigger the DAG in Airflow UI.
# 3. Check the output table in BigQuery.
# 4. Verify the exported file in the GCS bucket.

from datetime import datetime

from airflow import DAG
from airflow.models import Variable
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.bigquery_to_gcs import (
    BigQueryToGCSOperator,
)

# Example 1: Export High-Value Customers to Cloud Storage
high_value_customers_dag = DAG(
    "export_high_value_customers",
    default_args={"owner": "marketing-team", "start_date": datetime(2024, 1, 1)},
    description="Find high-value customers and export to GCS for campaign targeting",
    catchup=False,
    tags=["marketing", "export"],
)

# Read GCP project ID from Airflow Variable
PROJECT_ID = Variable.get("gcp_project_id")

# Query to identify high-value customers
identify_high_value_customers = BigQueryInsertJobOperator(
    task_id="find_high_value_customers",
    configuration={
        "query": {
            "query": (
                """
                WITH
                christmas_orders AS (
                SELECT
                    order_num,
                    cust_id
                FROM
                    `roi-bq-demos.bq_demo_small.order` o
                WHERE
                    o.order_date >= "2018-12-18"
                    AND o.order_date <= "2018-12-23" )
                SELECT
                    c.cust_id,
                    SUM(li.qty * p.prod_price) AS total_purchases
                FROM
                    christmas_orders co
                JOIN
                    roi-bq-demos.bq_demo_small.line_item li
                ON
                    co.order_num = li.order_num
                JOIN
                    roi-bq-demos.bq_demo_small.customer c
                ON
                    c.cust_id = co.cust_id
                JOIN
                    roi-bq-demos.bq_demo_small.product p
                ON
                    p.prod_code = li.prod_code
                GROUP BY
                    c.cust_id
                ORDER BY
                    total_purchases desc
                LIMIT 100
                """
            ),
            "useLegacySql": False,
            "destinationTable": {
                "projectId": PROJECT_ID,
                "datasetId": "marketing",
                "tableId": "high_value_customers",
            },
            "writeDisposition": "WRITE_TRUNCATE",
        }
    },
    dag=high_value_customers_dag,
)

# Export results to Cloud Storage for marketing campaign
export_to_gcs = BigQueryToGCSOperator(
    task_id="export_customer_list",
    source_project_dataset_table=f"{PROJECT_ID}.marketing.high_value_customers",
    destination_cloud_storage_uris=[f"gs://{PROJECT_ID}/high-value-customers.csv"],
    export_format="CSV",
    dag=high_value_customers_dag,
)

identify_high_value_customers >> export_to_gcs
