#!/usr/bin/env bash
#
# Deploy the custom server to Cloud Run and show how to read its logs.
# This is an OPTIONAL step. Every example runs locally without it.
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

# --- Option A: let ADK generate and deploy the container (simplest) ----------
# ADK builds an api_server container for the agent and deploys it. Cloud Run
# ingests stdout into Cloud Logging automatically. Traps covered in the tutorial:
#   * --log_level here feeds gcloud's own --verbosity, NOT the deployed app; the
#     generated container runs at INFO regardless, so set app log level in code.
#   * use --otel_to_cloud (not the deprecated --trace_to_cloud) to export telemetry.
#   * the container's deps come from demo_agent/requirements.txt, NOT the
#     requirements.txt at the project root. Since --otel_to_cloud makes ADK
#     import the OTel exporters at startup, they must be listed in that file or
#     the container crashes on boot with ModuleNotFoundError.
#   * MODEL_LOCATION is separate from REGION: the model lives in `global` while
#     the service runs in us-central1. Get this wrong and the deploy succeeds,
#     then every /run returns 500 with a 404 for the model.
#   * an agent-local .env is NOT enough. ADK does copy and load it, but it then
#     re-applies any variable already in the environment on top (envs.py), and
#     Cloud Run already provides GOOGLE_CLOUD_LOCATION. The .env value loses.
#     Real Cloud Run env vars are what win, and `adk deploy cloud_run` has no
#     flag for them, so they are set in a second step below.
MODEL_LOCATION="${MODEL_LOCATION:-global}"

adk deploy cloud_run \
  --project="$PROJECT_ID" --region="$REGION" \
  --service_name="$SERVICE" \
  --otel_to_cloud \
  ./demo_agent

# Vertex config, applied as real Cloud Run env vars so they beat both the
# container defaults and anything in a copied .env.
gcloud run services update "$SERVICE" \
  --project="$PROJECT_ID" --region="$REGION" --quiet \
  --update-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION}"

# --- Option B: deploy the hand-written server (examples/07) from source -------
# `gcloud run deploy --source` auto-detects a Dockerfile at the build root, so
# copy deploy/Dockerfile to the project root first (or run from a dir that has
# it as ./Dockerfile). This gives you the JSON-with-trace formatter from 07.
#
#   cp deploy/Dockerfile ./Dockerfile
#   gcloud run deploy "$SERVICE" \
#     --project="$PROJECT_ID" --region="$REGION" \
#     --source=. --allow-unauthenticated \
#     --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=global"

# `adk deploy` catches gcloud's failure and returns 0 anyway, so `set -e` will
# not stop us here. A failed deploy also leaves the service record behind, so
# "does the service exist" is not a real check; ask whether it is actually
# serving traffic.
READY=$(gcloud run services describe "$SERVICE" \
          --project="$PROJECT_ID" --region="$REGION" \
          --format='value(status.conditions.filter("type=Ready").extract(status))' 2>/dev/null || true)
if [[ "$READY" != *True* ]]; then
  echo
  echo "Deploy FAILED: service '$SERVICE' is not ready (Ready=${READY:-missing})." >&2
  echo "Check the build log first (pip install failures show up there):" >&2
  echo "  gcloud builds list --project=$PROJECT_ID --region=$REGION --limit=1" >&2
  echo "Then container startup errors:" >&2
  gcloud logging read \
    "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"$SERVICE\" severity=ERROR" \
    --project="$PROJECT_ID" --limit=1 --format='value(textPayload)' --freshness=10m >&2
  exit 1
fi

# A ready service can still 500 on every turn (wrong model region, missing
# permissions). Run one real turn before declaring victory.
URL=$(gcloud run services describe "$SERVICE" \
        --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')
TOKEN=$(gcloud auth print-identity-token)
SID="smoke-$$"
curl -fsS -X POST "$URL/apps/demo_agent/users/u1/sessions/$SID" \
     -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
     -d '{}' >/dev/null
CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$URL/run" \
        -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
        -d "{\"app_name\":\"demo_agent\",\"user_id\":\"u1\",\"session_id\":\"$SID\",
             \"new_message\":{\"role\":\"user\",\"parts\":[{\"text\":\"What's the weather in Tokyo?\"}]}}")
if [[ "$CODE" != "200" ]]; then
  echo "Smoke test FAILED: POST /run returned $CODE. Recent error:" >&2
  gcloud logging read \
    "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"$SERVICE\" severity>=ERROR" \
    --project="$PROJECT_ID" --limit=1 --format='value(textPayload)' --freshness=5m >&2 | tail -3
  exit 1
fi

echo
echo "Deployed and smoke-tested ($URL). Read structured logs (each line is one JSON entry):"
echo
cat <<EOF
  # Tail recent logs for the service:
  gcloud run services logs read "$SERVICE" --project="$PROJECT_ID" --region="$REGION" --limit=50

  # Or query in Cloud Logging by severity and trace:
  gcloud logging read \\
    'resource.type="cloud_run_revision" resource.labels.service_name="$SERVICE" severity>=INFO' \\
    --project="$PROJECT_ID" --limit=20 --format=json

  # Because every line carries logging.googleapis.com/trace, opening one request
  # in the Logs Explorer and clicking its trace shows all logs for that request.
EOF
