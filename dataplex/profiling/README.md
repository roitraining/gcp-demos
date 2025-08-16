### Dataplex Data Profiling Demonstration

This document provides a simplified, but realistic, demonstration of how Dataplex can be used for data profiling and quality checks in a production environment.

#### 1. Simplified Data Engineer Workflow

This workflow models a common scenario where a data engineer needs to validate new data from an external source before it can be used for downstream analytics.

**Scenario:** A company receives daily sales data as a CSV file in a Google Cloud Storage (GCS) bucket. The data engineering team must ensure the data is complete, has the correct data types, and meets business rules before it's moved to a data warehouse.

**Workflow Stages:**

1.  **Ingestion:** A partner uploads a CSV file (`sales_data.csv`) to a designated **raw GCS bucket**.
2.  **Data Discovery & Profiling (Dataplex):** A **Dataplex discovery job** automatically scans the GCS bucket. When a new file is detected, it triggers a **data profiling task**.
      * **Goal:** Automatically analyze the structure, data types, value distributions, and potential anomalies in the new data.
3.  **Quality Check & Validation (Dataplex Data Quality):** A **Dataplex data quality scan** runs on the profiled data to enforce business rules.
      * **Goal:** Validate specific rules, such as "the `transaction_id` column must not contain null values."
4.  **Action:**
      * **Success:** If the data passes the quality checks, it's considered clean and ready for analysis.
      * **Failure:** If the data fails, a data engineer is alerted to investigate the data quality issue.
5.  **Preparation for Analytics:** The validated, clean data is now ready for use by business analysts and data scientists.

-----

#### 2\. Step-by-Step Demonstration Instructions

This guide will walk you through setting up the core Dataplex components and then simulating the ingestion of data to see the process in action.

**Prerequisites:**

  * A Google Cloud Project with billing enabled.
  * The `gcloud` CLI installed and authenticated.
  * Terraform installed.
  * Necessary IAM roles for your user account (e.g., `Owner` or `Project Editor` for a demo environment).

**Step 1: Set Up the Project with Terraform**

1.  Create a new directory for your Terraform code.

2.  Create the `main.tf` and `dataplex.tf` files with the code provided below.

3.  Replace `your-gcp-project-id` with your actual project ID in `main.tf`.

4.  Open a terminal in your project directory and run the following commands:

    ```bash
    terraform init
    terraform apply
    ```

5.  When prompted, type `yes` to approve the creation of the resources. The output will show the names of the resources created, including the raw GCS bucket.

**Step 2: Generate Sample Data**

1.  Create a CSV file named `sales_data.csv` with the following content. This represents our "good" data.

    ```csv
    transaction_id,product_sku,sale_amount,sale_date
    1001,SKU-A,12.50,2025-08-01
    1002,SKU-B,25.00,2025-08-01
    1003,SKU-A,12.50,2025-08-02
    1004,SKU-C,75.25,2025-08-02
    ```

**Step 3: Trigger the Workflow (Simulated Ingestion)**

1.  Upload the `sales_data.csv` file to the GCS bucket created by Terraform. Find the bucket name in the Terraform output (it will be `demo-raw-bucket-<project_id>`).

    ```bash
    gcloud storage cp sales_data.csv gs://<your-raw-bucket-name>/sales/sales_data.csv
    ```

**Step 4: Observe Dataplex in the Console**

1.  Navigate to the **Dataplex** UI in the Google Cloud Console.
2.  Click on your lake, zone, and asset.
3.  In the asset details, you'll see a **Profiling** tab. Within a few minutes, the discovery and profiling job will have run on your new file.
4.  On the **Profiling** tab, you'll see a detailed analysis of your data:
      * **Data Types:** Confirm that `transaction_id` is an `INTEGER`, `sale_amount` is a `FLOAT`, and `sale_date` is a `DATE` or `TIMESTAMP`.
      * **Statistics:** See metrics like mean, min, max, and standard deviation.
      * **Value Distribution:** View the distribution of values for each column.
      * **Null Count:** Observe that the `transaction_id` column has a null count of 0.

**Step 5: Inspect the Data Quality Scan Results**

1.  Go to the **Data quality scans** section in the Dataplex UI.
2.  Find the scan you created (`sales-data-quality-scan`).
3.  Click on the scan to view the results. The scan should show a **Success** status, indicating that the `NOT_NULL` check passed.

**Step 6: Demonstrate a Failure Scenario (Optional)**

1.  Create a new CSV file named `bad_sales_data.csv` that contains a null value in the `transaction_id` column.

    ```csv
    transaction_id,product_sku,sale_amount,sale_date
    1005,SKU-D,50.00,2025-08-03
    ,SKU-E,15.25,2025-08-03
    ```

2.  Upload this file to the GCS bucket:

    ```bash
    gcloud storage cp bad_sales_data.csv gs://<your-raw-bucket-name>/sales/bad_sales_data.csv
    ```

3.  Wait for the discovery and profiling jobs to run.

4.  Check the **Data quality scans** again. The new run of the `sales-data-quality-scan` should show a **Failure** status due to the null value.
