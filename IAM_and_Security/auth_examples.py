"""
BigQuery Authentication Methods Demo

This script demonstrates three different ways to authenticate with BigQuery:

1. Application Default Credentials (ADC).
2. Service Account Key File
3. Service Account Impersonation

Requirements:
- pip install google-cloud-bigquery google-auth
- For ADC
    - Make sure your user account has the necessary permissions.
    - Run 'gcloud auth application-default login' or set GOOGLE_APPLICATION_CREDENTIALS
- For Service Account key file
    - Create a service account with appropriate permissions
    - Create and download a keyfile
    - Update 'key_path' variable with your key file path
- For Service Account Impersonation
    - Make sure your user account has the "Service Account Token Creator" role on the target service account
    - Update 'target_service_account' variable with the email of the service account to impersonate

Variations
- You can configure ADC to use a service account with key file
- You can configure ADC to use impersonation as default
"""

import os
from google.cloud import bigquery
from google.auth import default, impersonated_credentials
from google.oauth2 import service_account
import json

# Query to execute
QUERY = "SELECT COUNT(*) as row_count FROM `roi-bq-demos.bq_demo.line_item`"


def execute_query_with_client(client, method_name):
    """Execute the query and print results"""
    try:
        print(f"\n--- {method_name} ---")
        query_job = client.query(QUERY)
        results = query_job.result()

        for row in results:
            print(f"Row count: {row.row_count}")

        print(f"✓ {method_name} completed successfully")

    except Exception as e:
        print(f"✗ {method_name} failed: {str(e)}")


def method_1_application_default_credentials():
    """Method 1: Use Application Default Credentials (ADC)"""
    try:
        # This will use ADC - credentials from:
        # 1. GOOGLE_APPLICATION_CREDENTIALS environment variable
        # 2. gcloud auth application-default login
        # 3. Compute Engine/Cloud Run/GKE metadata service
        client = bigquery.Client()
        execute_query_with_client(client, "Application Default Credentials")

    except Exception as e:
        print(f"✗ Application Default Credentials setup failed: {str(e)}")


def method_2_service_account_key():
    """Method 2: Use Service Account Key File"""
    # Update this path to your service account key file
    key_path = "path/to/your/service-account-key.json"

    try:
        if not os.path.exists(key_path):
            print(f"✗ Service account key file not found: {key_path}")
            print("  Please update the 'key_path' variable with the correct path")
            return

        credentials = service_account.Credentials.from_service_account_file(key_path)
        client = bigquery.Client(credentials=credentials)
        execute_query_with_client(client, "Service Account Key")

    except Exception as e:
        print(f"✗ Service Account Key method failed: {str(e)}")


def method_3_service_account_impersonation():
    """Method 3: Use Service Account Impersonation"""
    # Update this with the service account email you want to impersonate
    target_service_account = "your-service-account@your-project.iam.gserviceaccount.com"

    try:
        # Get source credentials (usually from ADC)
        source_credentials, project = default()

        # Create impersonated credentials
        target_credentials = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=target_service_account,
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        client = bigquery.Client(credentials=target_credentials)
        execute_query_with_client(client, "Service Account Impersonation")

    except Exception as e:
        print(f"✗ Service Account Impersonation failed: {str(e)}")


def main():
    """Main function to run all authentication methods"""
    print("BigQuery Authentication Methods Demo")
    print("=" * 50)

    # Method 1: Application Default Credentials
    method_1_application_default_credentials()

    # Method 2: Service Account Key
    method_2_service_account_key()

    # Method 3: Service Account Impersonation
    method_3_service_account_impersonation()

    print("\n" + "=" * 50)
    print("Demo completed!")


if __name__ == "__main__":
    main()
