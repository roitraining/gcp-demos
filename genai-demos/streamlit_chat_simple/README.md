# Simple Streamlit Chat App w/PaLM APIs

This is a very simple application that uses **Streamlit** and the Google Cloud
Client Library for **Vertex AI**. It offers a chat interface that leverages
the PaLMv2 chat model to generate responses.

The application makes use of the client library's message history feature
in conjunction with Streamlit's state management.

Included in the repo is the source code along with files required to 
deploy to **Cloud Run**.

## Setup

1. Enable required services
   ```bash
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable artifactregistry.googleapis.com
    gcloud services enable aiplatform.googleapis.com
    gcloud services enable compute.googleapis.com
   ```

2. Add permissions to cloud build service
    ```bash
    PROJECT_ID=$(gcloud config get-value project)
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID \
        --format='value(projectNumber)')
    SERVICE_ACCOUNT="$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"

    gcloud projects add-iam-policy-binding \
        $PROJECT_ID \
        --member=serviceAccount:$SERVICE_ACCOUNT \
        --role=roles/run.admin
    gcloud projects add-iam-policy-binding \
        $PROJECT_ID \
        --member=serviceAccount:$SERVICE_ACCOUNT \
        --role=roles/artifactregistry.admin
    gcloud services add-iam-policy-binding \
        $SERVICE_ACCOUNT \
        --member=serviceAccount:$PROJECT_NUMER-compute@developer.gserviceaccount.com \
        --role=roles/iam.serviceaccounts.actAs
    ```

3. Create a repository for application container
    ```bash
    gcloud artifacts repositories create chat \
        --repository-format=Docker \
        --location=us-central1
    ```

4. Create a Cloud Build job generate the image, upload, and deploy the
   Clour Run service
   ```bash
    gcloud builds submit . --config=cloudbuild.yaml
   ```

##Cleanup

1. Delete the Cloud Run service
   ```bash
   gcloud run services delete chat --region us-central1 --platform managed --quiet
   ```