 #!/bin/bash

export PROJECT_ID=$(gcloud config get-value project)

python -m venv .venv
source .venv/bin/activate 
pip install -r req1.txt
pip install -r req2.txt

gcloud iam service-accounts create $1  \
    --display-name="$1"
sleep 2
export sa_email=$(gcloud iam service-accounts list --filter="displayName:$1" --format="value(email)")
gcloud projects add-iam-policy-binding $PROJECT_ID\
    --member="serviceAccount:$sa_email" \
    --role="roles/editor"
gcloud iam service-accounts keys create $1.json --iam-account=$sa_email
export GOOGLE_APPLICATION_CREDENTIALS=$1.json

gsutil mb -l us-central1 "gs://$PROJECT_ID-dflow-demo"

gcloud services disable dataflow
sleep 5
gcloud services enable  bigquery pubsub dataflow