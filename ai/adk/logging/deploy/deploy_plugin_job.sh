#!/usr/bin/env bash
#
# Tutorial 3.2, 3.4, and 4: deploy a plugin example script as a Cloud Run JOB and
# execute it once, to see what its plugin sends to Cloud Logging. Each script runs
# once and exits, so a Job is the honest fit (a Service would fail its readiness
# check with no port). One image serves every script; the script to run is the
# Job argument. OPTIONAL step.
#
# Usage:
#   export PROJECT_ID=your-project
#   export REGION=us-central1
#
#   # 3.2 -- LoggingPlugin, run at INFO then WARNING:
#   SCRIPT=examples/03_logging_plugin.py ./deploy/deploy_plugin_job.sh
#   gcloud run jobs execute adk-plugin-job --project="$PROJECT_ID" \
#     --region="$REGION" --update-env-vars=LOG_LEVEL=WARNING --wait
#
#   # 3.4 -- DebugLoggingPlugin, capture to a mounted Cloud Storage bucket:
#   export BUCKET="${PROJECT_ID}-adk-debug"
#   MOUNT=1 SCRIPT=examples/04_debug_plugin.py ./deploy/deploy_plugin_job.sh
#   gcloud storage cat "gs://$BUCKET/adk_debug.yaml" | head -40
#
#   # 4 -- StructuredTelemetryPlugin, then query the structured fields:
#   SCRIPT=examples/05_structured_plugin.py ./deploy/deploy_plugin_job.sh
#   gcloud logging read \
#     'resource.type="cloud_run_job" jsonPayload.event="tool_end"' \
#     --project="$PROJECT_ID" --freshness=15m \
#     --format='table(jsonPayload.tool, jsonPayload.latency_ms, jsonPayload.status)'
#
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-us-central1}"
MODEL_LOCATION="${MODEL_LOCATION:-global}"
SCRIPT="${SCRIPT:-examples/03_logging_plugin.py}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Job name derives from the script so 03 and 04 get distinct jobs by default.
case "$SCRIPT" in
  *04_debug_plugin.py)      DEFAULT_JOB="adk-debug-plugin-job" ;;
  *05_structured_plugin.py) DEFAULT_JOB="adk-structured-job" ;;
  *)                        DEFAULT_JOB="adk-plugin-job" ;;
esac
JOB="${JOB:-$DEFAULT_JOB}"

# Run from the folder root so the build context has demo_agent/ and examples/.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# `gcloud run ... --source` auto-detects ./Dockerfile at the build root. Put
# ours there for the build, and remove it afterward whether or not we succeed.
cp deploy/Dockerfile.plugin_job ./Dockerfile
trap 'rm -f "$ROOT/Dockerfile"' EXIT

ENV_VARS="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION},LOG_LEVEL=${LOG_LEVEL}"

# Optional Cloud Storage volume so a file-writing plugin (example 04) survives
# the execution. Without it, the Job's filesystem is discarded on exit.
VOLUME_ARGS=()
if [[ "${MOUNT:-}" == "1" ]]; then
  BUCKET="${BUCKET:-${PROJECT_ID}-adk-debug}"
  if ! gcloud storage buckets describe "gs://$BUCKET" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo "Creating bucket gs://$BUCKET in $REGION..."
    gcloud storage buckets create "gs://$BUCKET" --project="$PROJECT_ID" --location="$REGION"
  fi
  ENV_VARS="${ENV_VARS},DEBUG_OUTPUT=/mnt/out/adk_debug.yaml"
  VOLUME_ARGS=(
    "--add-volume=name=out,type=cloud-storage,bucket=$BUCKET"
    "--add-volume-mount=volume=out,mount-path=/mnt/out"
  )
fi

echo "Deploying Cloud Run Job '$JOB' to run '$SCRIPT' (LOG_LEVEL=$LOG_LEVEL)..."
gcloud run jobs deploy "$JOB" \
  --project="$PROJECT_ID" --region="$REGION" \
  --source=. \
  --args="$SCRIPT" \
  --set-env-vars="$ENV_VARS" \
  ${VOLUME_ARGS[@]+"${VOLUME_ARGS[@]}"}

echo
echo "Executing job (waits for completion)..."
gcloud run jobs execute "$JOB" --project="$PROJECT_ID" --region="$REGION" --wait

cat <<EOF

Done. The script's stdout/stderr went to Cloud Logging. Read it back:

  gcloud logging read \\
    'resource.type="cloud_run_job" resource.labels.job_name="$JOB"' \\
    --project="$PROJECT_ID" --limit=60 --format='table(severity,textPayload)' --freshness=15m

  # Re-run at a different level without redeploying (example 03):
  gcloud run jobs execute "$JOB" --project="$PROJECT_ID" --region="$REGION" \\
    --update-env-vars=LOG_LEVEL=WARNING --wait

  # Tear down:
  gcloud run jobs delete "$JOB" --project="$PROJECT_ID" --region="$REGION" --quiet
EOF
