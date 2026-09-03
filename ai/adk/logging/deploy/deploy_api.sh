#!/usr/bin/env bash
#
# Tutorial 1.5: deploy the minimal API server (examples/09_min_api.py) as a
# Cloud Run SERVICE, to see the raw Part 1 logs (yours, google_adk, and uvicorn
# access lines, all plain text) land in Cloud Logging. OPTIONAL step.
#
# Usage:
#   export PROJECT_ID=your-project
#   export REGION=us-central1
#   ./deploy/deploy_api.sh                 # deploy at LOG_LEVEL=info
#   LOG_LEVEL=warning ./deploy/deploy_api.sh
#
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-adk-logging-api}"
LOG_LEVEL="${LOG_LEVEL:-info}"
MODEL_LOCATION="${MODEL_LOCATION:-global}"

# Run from the folder root so the build context has demo_agent/ and examples/.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# `gcloud run deploy --source` auto-detects ./Dockerfile at the build root.
cp deploy/Dockerfile.api ./Dockerfile
trap 'rm -f "$ROOT/Dockerfile"' EXIT

echo "Deploying Cloud Run service '$SERVICE' at LOG_LEVEL=$LOG_LEVEL..."
gcloud run deploy "$SERVICE" \
  --project="$PROJECT_ID" --region="$REGION" \
  --source=. \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION},LOG_LEVEL=${LOG_LEVEL}"

URL=$(gcloud run services describe "$SERVICE" \
        --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')

echo
echo "Smoke-testing $URL/chat ..."
CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$URL/chat" \
        -H 'content-type: application/json' \
        -d '{"message":"What'\''s the weather in Tokyo?"}')
if [[ "$CODE" != "200" ]]; then
  echo "Smoke test FAILED: POST /chat returned $CODE. Recent error:" >&2
  gcloud logging read \
    "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"$SERVICE\" severity>=ERROR" \
    --project="$PROJECT_ID" --limit=3 --format='value(textPayload)' --freshness=5m >&2
  exit 1
fi

cat <<EOF

Deployed and smoke-tested. Service URL: $URL

Send a turn:
  curl -s -X POST "$URL/chat" -H 'content-type: application/json' \\
       -d '{"message":"What'\''s the weather in Tokyo?"}'

Read the raw logs. Note this server does NOTHING clever: plain-text lines from
basicConfig, and uvicorn's default access lines. In Cloud Logging you will see
all three streams, unstructured, and the basicConfig lines (on stderr) show as
ERROR severity. That is the "before" the rest of the tutorial fixes.

  gcloud run services logs read "$SERVICE" \\
    --project="$PROJECT_ID" --region="$REGION" --limit=40

  # Or in Cloud Logging, watch the severity column:
  gcloud logging read \\
    'resource.type="cloud_run_revision" resource.labels.service_name="$SERVICE"' \\
    --project="$PROJECT_ID" --limit=40 --format='table(severity,textPayload)' --freshness=10m

Change the level (redeploy, since level is read once at startup):
  LOG_LEVEL=warning ./deploy/deploy_api.sh

Tear down:
  gcloud run services delete "$SERVICE" --project="$PROJECT_ID" --region="$REGION" --quiet
EOF
