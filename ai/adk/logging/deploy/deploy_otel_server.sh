#!/usr/bin/env bash
#
# Tutorial 5.5, Step 4: deploy the minimal OTel server (examples/08_otel_server.py)
# to Cloud Run as a SERVICE. The image bakes no .env, so the model config, the
# content setting, and the experimental event format go in --set-env-vars.
# OPTIONAL step.
#
# Usage:
#   export PROJECT_ID=your-project
#   export REGION=us-central1
#   ./deploy/deploy_otel_server.sh
#
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-adk-otel-server}"
MODEL_LOCATION="${MODEL_LOCATION:-global}"

# Run from the folder root so the build context has demo_agent/ and examples/.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# `gcloud run deploy --source` auto-detects ./Dockerfile at the build root. Put
# ours there for the build, and remove it afterward whether or not we succeed.
cp deploy/Dockerfile.otel_server ./Dockerfile
trap 'rm -f "$ROOT/Dockerfile"' EXIT

echo "Deploying Cloud Run service '$SERVICE'..."
gcloud run deploy "$SERVICE" \
  --project="$PROJECT_ID" --region="$REGION" \
  --source=. \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION},OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT,OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental"

# A ready service can still 500 on every turn. Run one real turn before
# declaring victory.
URL=$(gcloud run services describe "$SERVICE" \
        --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')

echo
echo "Smoke-testing $URL/chat ..."
CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$URL/chat" \
        -H 'content-type: application/json' \
        -d '{"message":"What'\''s the weather in London?"}')
if [[ "$CODE" != "200" ]]; then
  echo "Smoke test FAILED: POST /chat returned $CODE." >&2
  exit 1
fi

cat <<EOT

Deployed and smoke-tested. Service URL: $URL

Tear down:
  gcloud run services delete "$SERVICE" --project="$PROJECT_ID" --region="$REGION" --quiet
EOT
