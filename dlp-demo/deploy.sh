#!/bin/bash

# Deploy script for DLP Demo to Cloud Run
set -e

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="dlp-demo"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}:latest"

echo "Deploying DLP Demo to Cloud Run..."
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service Name: ${SERVICE_NAME}"

# Ensure we're using the correct project
gcloud config set project ${PROJECT_ID}

# Build and push the container image
echo "Building container image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --port 8080

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)')

echo ""
echo "Deployment complete!"
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "To test the service:"
echo "curl ${SERVICE_URL}/health"
