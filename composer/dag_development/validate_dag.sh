# In your environment's bucket, create a test directory and copy your DAGs to it.
gcloud storage cp gs://us-central1-example-environment-a12bc345-bucket/dags \
  gs://us-central1-example-environment-a12bc345-bucket/data/test --recursive

# Test for errors in all your DAGs
gcloud storage cp gs://us-central1-example-environment-a12bc345-bucket/dags \
  gs://us-central1-example-environment-a12bc345-bucket/data/test --recursive

# Test a task for errors
gcloud composer environments run \
  ENVIRONMENT_NAME \
  --location ENVIRONMENT_LOCATION \
  tasks test -- --subdir /home/airflow/gcs/data/test \
  DAG_ID TASK_ID \
  DAG_EXECUTION_DATE