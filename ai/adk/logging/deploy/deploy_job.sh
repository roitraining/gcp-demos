#!/usr/bin/env bash
#
# Tutorial 1.4: deploy the plain script (examples/01_log_levels.py) as a
# Cloud Run JOB and execute it, to see whether its console logs reach Cloud
# Logging and at what severity. The script runs once and exits, so a Job is the
# honest fit; a Service would fail its readiness check (no port). OPTIONAL step.
#
# Usage:
#   export PROJECT_ID=your-project
#   export REGION=us-central1
#   ./deploy/deploy_job.sh                 # deploy, then execute at info
#   LEVEL=warning ./deploy/deploy_job.sh   # deploy, then execute at warning
#
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-us-central1}"
JOB="${JOB:-adk-logging-job}"
LEVEL="${LEVEL:-info}"
MODEL_LOCATION="${MODEL_LOCATION:-global}"

# Run from the folder root so the build context has demo_agent/ and examples/.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# `gcloud run ... --source` auto-detects ./Dockerfile at the build root. Put
# ours there for the build, and remove it afterward whether or not we succeed.
cp deploy/Dockerfile.job ./Dockerfile
trap 'rm -f "$ROOT/Dockerfile"' EXIT

echo "Deploying Cloud Run Job '$JOB' (level passed at execution time)..."
gcloud run jobs deploy "$JOB" \
  --project="$PROJECT_ID" --region="$REGION" \
  --source=. \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION}"

echo
echo "Executing job at LEVEL=$LEVEL (waits for completion)..."
gcloud run jobs execute "$JOB" \
  --project="$PROJECT_ID" --region="$REGION" \
  --args="$LEVEL" --wait

cat <<EOF

Done. The script's stdout/stderr went to Cloud Logging. Read it back:

  # All logs for this job's executions:
  gcloud logging read \\
    'resource.type="cloud_run_job" resource.labels.job_name="$JOB"' \\
    --project="$PROJECT_ID" --limit=30 --format='table(severity,textPayload)' --freshness=10m

Watch the SEVERITY column. Because 01_log_levels.py uses logging.basicConfig,
its records are written to stderr, which Cloud Run records as ERROR severity
regardless of the record's own level (the print()ed answer, on stdout, comes
through as Default/INFO). That mismatch is the problem Part 4 fixes with JSON
on stdout and an explicit severity field.

  # Re-run at a different level without redeploying:
  gcloud run jobs execute "$JOB" --project="$PROJECT_ID" --region="$REGION" \\
    --args=warning --wait

  # Tear down:
  gcloud run jobs delete "$JOB" --project="$PROJECT_ID" --region="$REGION" --quiet
EOF
