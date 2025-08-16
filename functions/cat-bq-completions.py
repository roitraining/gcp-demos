import json
import base64
from datetime import datetime
from google.cloud import storage
import functions_framework


@functions_framework.cloud_event
def process_bigquery_job_completion(cloud_event):
    """
    Processes BigQuery job completion events from Pub/Sub and writes details to Cloud Storage.

    Triggered by Pub/Sub messages containing BigQuery audit logs.
    """

    # Log the incoming event for debugging
    log_entry = None
    # Try to handle different event structures
    if "data" in cloud_event.data:
        # Standard Pub/Sub trigger
        try:
            message_data = base64.b64decode(cloud_event.data["data"]).decode("utf-8")
            log_entry = json.loads(message_data)
        except Exception as e:
            print(f"Error decoding message: {e}")
            return
    elif "message" in cloud_event.data and "data" in cloud_event.data["message"]:
        # Eventarc Pub/Sub trigger
        try:
            message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode(
                "utf-8"
            )
            log_entry = json.loads(message_data)
        except Exception as e:
            print(f"Error decoding message: {e}")
            return
    else:
        print("No data found in cloud event. Event structure:", cloud_event.data)
        return

    try:

        # Write to Cloud Storage
        write_to_cloud_storage(
            bucket_name="jwd-gcp-demos",
            file_path=f"bigquery-jobs/{datetime.now().strftime('%Y/%m/%d')}/job-completions.log",
            content=json.dumps(log_entry, indent=2),
        )

        print(f"Successfully processed job completion for {job_info['job_id']}")

    except Exception as e:
        print(f"Error processing BigQuery job completion: {str(e)}")
        print(f"Raw log entry: {json.dumps(log_entry, indent=2)}")


def write_to_cloud_storage(bucket_name, file_path, content):
    """
    Write content to Cloud Storage, appending to existing file if it exists.
    """
    try:
        # Initialize the Cloud Storage client
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)

        # Upload the updated content
        blob.upload_from_string(content, content_type="application/json")

        print(f"Successfully wrote job data to gs://{bucket_name}/{file_path}")

    except Exception as e:
        print(f"Error writing to Cloud Storage: {str(e)}")
        raise


# Optional: Add requirements.txt content
"""
requirements.txt:
google-cloud-storage>=2.10.0
functions-framework>=3.0.0
"""
