#!/usr/bin/env bash
#
# Part 4: deploy the custom server (examples/06_custom_server.py) to Cloud Run
# as a SERVICE, so the structured JSON logging you ran locally lands in Cloud
# Logging with correct severity and per-request trace grouping. OPTIONAL step.
#
# Usage:
#   export PROJECT_ID=your-project
#   export REGION=us-central1
#   ./deploy/deploy_cloudrun.sh
#
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-adk-logging-demo}"
# The model lives in `global` while the service runs in us-central1. Get this
# wrong and the deploy succeeds, then every /chat returns 500 with a 404 for the
# model. This is set as a real Cloud Run env var below so it beats any default.
MODEL_LOCATION="${MODEL_LOCATION:-global}"

# Run from the folder root so the build context has demo_agent/ and examples/.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# `gcloud run deploy --source` auto-detects ./Dockerfile at the build root.
cp deploy/Dockerfile ./Dockerfile
trap 'rm -f "$ROOT/Dockerfile"' EXIT

echo "Deploying Cloud Run service '$SERVICE'..."
gcloud run deploy "$SERVICE" \
  --project="$PROJECT_ID" --region="$REGION" \
  --source=. \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION}"

# A ready service can still 500 on every turn (wrong model region, missing
# permissions). Run one real turn before declaring victory.
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
    --project="$PROJECT_ID" --limit=3 --format='value(jsonPayload.message,textPayload)' --freshness=5m >&2
  exit 1
fi

echo
echo "Deployed and smoke-tested ($URL). Read structured logs (each line is one JSON entry):"
echo
cat <<EOF
  # Send a turn, passing the trace header the way Cloud Run does for you:
  curl -s -X POST "$URL/chat" -H 'content-type: application/json' \\
       -H 'X-Cloud-Trace-Context: 105445aa7843bc8bf206b12000100000/1;o=1' \\
       -d '{"message":"What'\''s the weather in Tokyo?"}'

  # Tail recent logs for the service:
  gcloud run services logs read "$SERVICE" --project="$PROJECT_ID" --region="$REGION" --limit=50

  # Severity is now a field you set, not a guess: every line reads its real level.
  gcloud logging read \\
    'resource.type="cloud_run_revision" resource.labels.service_name="$SERVICE" severity>=INFO' \\
    --project="$PROJECT_ID" --limit=20 \\
    --format='table(severity, jsonPayload.message)' --freshness=10m

  # Your plugin's fields are queryable columns, not text you have to parse:
  gcloud logging read \\
    'resource.type="cloud_run_revision" jsonPayload.event="tool_end"' \\
    --project="$PROJECT_ID" --limit=5 \\
    --format='table(jsonPayload.tool, jsonPayload.latency_ms, jsonPayload.status)' --freshness=10m

  # Because every line carries logging.googleapis.com/trace, opening one request
  # in the Logs Explorer and clicking its trace shows all logs for that request.

Tear down:
  gcloud run services delete "$SERVICE" --project="$PROJECT_ID" --region="$REGION" --quiet
EOF
