#!/usr/bin/env bash
#
# Tutorial 1.7: build the minimal custom container and deploy it to Agent
# Runtime (bring-your-own-container). Unlike deploy_agent_engine.sh (which
# deploys the AGENT object via `adk deploy`), this ships OUR own FastAPI server
# (main.py) as a container. There is no gcloud CLI for Agent Runtime, so the
# registration step is a Python SDK call (deploy_byoc.py). OPTIONAL.
#
# Usage (run from this directory):
#   export PROJECT_ID=your-project
#   export LOCATION=us-central1
#   ./deploy_byoc.sh
#   LOG_LEVEL=warning ./deploy_byoc.sh
#
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
LOCATION="${LOCATION:-us-central1}"
REPO="${REPO:-adk-logging}"
IMAGE="${IMAGE:-adk-logging-byoc}"
LOG_LEVEL="${LOG_LEVEL:-info}"
MODEL_LOCATION="${MODEL_LOCATION:-global}"

cd "$(dirname "$0")"

IMAGE_URI="${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE}:latest"

# 1. Artifact Registry repo (idempotent).
if ! gcloud artifacts repositories describe "$REPO" \
      --project="$PROJECT_ID" --location="$LOCATION" >/dev/null 2>&1; then
  echo "Creating Artifact Registry repo '$REPO'..."
  gcloud artifacts repositories create "$REPO" \
    --project="$PROJECT_ID" --location="$LOCATION" \
    --repository-format=docker
fi

# 2. Build and push the image via Cloud Build.
echo "Building and pushing $IMAGE_URI ..."
gcloud builds submit --project="$PROJECT_ID" --region="$LOCATION" \
  --tag "$IMAGE_URI" .

# 2b. Grant the AI Platform service agents read access, or the platform cannot
# pull the image (FAILED_PRECONDITION at register time). Grant at the PROJECT
# level: a repo-scoped binding was NOT sufficient in testing (the -re agent's
# repo binding did not resolve; the project-level grant is what unblocked the
# pull). Ensure the agents exist first, then grant. Idempotent.
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
gcloud beta services identity create --service=aiplatform.googleapis.com \
  --project="$PROJECT_ID" >/dev/null 2>&1 || true
for SA in "service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
          "service-${PROJECT_NUMBER}@gcp-sa-aiplatform.iam.gserviceaccount.com"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA" \
    --role="roles/artifactregistry.reader" \
    --condition=None --quiet >/dev/null
done

# 3. Register the container as an Agent Runtime instance (Python SDK).
# Use the tutorial venv's python (it has the vertexai SDK); fall back to PYTHON
# override or plain python3 if the venv is elsewhere.
PYTHON="${PYTHON:-../.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then PYTHON=python3; fi
echo "Registering the container with Agent Runtime (using $PYTHON)..."
RESOURCE=$(PROJECT_ID="$PROJECT_ID" LOCATION="$LOCATION" IMAGE_URI="$IMAGE_URI" \
           LOG_LEVEL="$LOG_LEVEL" MODEL_LOCATION="$MODEL_LOCATION" \
           "$PYTHON" deploy_byoc.py)

echo
echo "Deployed. Reasoning engine resource:"
echo "  $RESOURCE"
cat <<EOF

Query it through the /api passthrough (note the doubled /api/api: the passthrough
prefix + the container's own /api route), then read the logs:

  ACCESS_TOKEN=\$(gcloud auth print-access-token)
  curl -s -X POST \\
    "https://${LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/${RESOURCE}/api/api/stream_reasoning_engine" \\
    -H "Authorization: Bearer \$ACCESS_TOKEN" \\
    -H 'content-type: application/json' \\
    -d '{"class_method":"async_stream_query","input":{"user_id":"u1","message":"What'\''s the weather in Tokyo?"}}'

  # Our naive Part 1 logs land under reasoning_engine_stdout. ENGINE_ID is the
  # last path segment of the resource name above.
  gcloud logging read \\
    'logName:"reasoning_engine_stdout" resource.labels.reasoning_engine_id="ENGINE_ID"' \\
    --project="$PROJECT_ID" --limit=30 --freshness=10m

Tear down (ENGINE_ID = last segment of the resource name):
  python -c "import vertexai; vertexai.Client(project='$PROJECT_ID', location='$LOCATION').agent_engines.delete(name='$RESOURCE', force=True)"
EOF
