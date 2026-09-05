#!/usr/bin/env bash
#
# Tutorial 5.4: ship stream 4 to Google Cloud from Cloud Run. `adk deploy
# cloud_run --otel_to_cloud` bakes the flag into the container's CMD line
# (cli_deploy.py:216), so the server inside Cloud Run installs the same
# exporters 5.2 installed on your laptop, this time under the service account's
# credentials. No agent code, no OTEL_* variables.
#
# Unlike the other scripts here this one copies no Dockerfile: `adk deploy`
# generates one into --temp_folder and builds from there.
#
# Usage:
#   export PROJECT_ID=your-project
#   export REGION=us-central1
#   ./deploy/deploy_otel_cloudrun.sh
#
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-adk-logging-otel}"
# The model lives in `global` while the service runs in us-central1. The
# generated Dockerfile hardcodes ENV GOOGLE_CLOUD_LOCATION to the *Cloud Run*
# region, so this has to be set as a real Cloud Run env var to beat it.
MODEL_LOCATION="${MODEL_LOCATION:-global}"

# Used as the startTime of the Cloud Trace query printed at the end.
START_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

TMP_BASE="${TMPDIR:-/tmp}"
TEMP_FOLDER="${TEMP_FOLDER:-${TMP_BASE%/}/adk_otel_cloudrun_$(date +%Y%m%d_%H%M%S)}"
DOCKERFILE_COPY="${TEMP_FOLDER}.Dockerfile"

# Run from the folder root: the agent path and the venv below are relative to it.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail() {
  echo "FAILED: $1" >&2
  echo "Recent ERROR logs for '$SERVICE':" >&2
  gcloud logging read \
    "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"$SERVICE\" severity>=ERROR" \
    --project="$PROJECT_ID" \
    --limit=5 \
    --format='value(textPayload,jsonPayload.message)' \
    --freshness=3m >&2
  exit 1
}

# `adk deploy` deletes --temp_folder when it exits (cli_deploy.py:946-948), so
# copy the generated Dockerfile out while the build is still running. Its CMD
# line is what 5.4 reads to show that --otel_to_cloud rode into the container.
(
  for _ in $(seq 1 300); do
    if [[ -f "$TEMP_FOLDER/Dockerfile" ]]; then
      cp "$TEMP_FOLDER/Dockerfile" "$DOCKERFILE_COPY"
      break
    fi
    sleep 1
  done
) &
COPIER_PID=$!
trap 'kill "$COPIER_PID" 2>/dev/null || true' EXIT

echo "Deploying Cloud Run service '$SERVICE' with --otel_to_cloud..."
# Everything after `--` is passed through to `gcloud run deploy` verbatim.
# demo_agent/.env ships inside the image, so the content knob it carries is
# deliberately NOT repeated here: 5.4 proves the file arrived by reading the
# llm_request span attribute back as {}.
./.venv/bin/adk deploy cloud_run \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --service_name="$SERVICE" \
  --otel_to_cloud \
  --temp_folder="$TEMP_FOLDER" \
  ./demo_agent \
  -- \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION}"

if [[ -f "$DOCKERFILE_COPY" ]]; then
  echo
  echo "Generated Dockerfile (saved from $TEMP_FOLDER before ADK removed it): $DOCKERFILE_COPY"
  grep '^CMD' "$DOCKERFILE_COPY" || true
fi

# `adk deploy` catches every exception and still exits 0 (cli_tools_click.py:2456),
# so a failed deploy looks like a successful script. Ask Cloud Run instead.
echo
echo "Checking the service..."
# Read the Ready condition from Cloud Run itself. extract() yields a list, so
# .flatten() is required or value() renders it as the literal "['True']" and the
# check never passes. A failed deploy leaves the service Ready=False (or absent),
# which this catches with an accurate message.
READY=$(gcloud run services describe "$SERVICE" \
          --project="$PROJECT_ID" \
          --region="$REGION" \
          --format='value(status.conditions.filter("type=Ready").extract("status").flatten())' 2>/dev/null || true)
[[ "$READY" == "True" ]] || fail "service '$SERVICE' is not Ready (condition: '${READY:-none; the deploy may not have created it}'). 'adk deploy' exits 0 even when the deploy failed, so read its output above."

URL=$(gcloud run services describe "$SERVICE" \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --format='value(status.url)' 2>/dev/null || true)
[[ -n "$URL" ]] || fail "service '$SERVICE' is Ready but has no URL."

# A ready service can still 500 on every turn (wrong model region, a dependency
# missing from demo_agent/requirements.txt). Run one real turn before declaring
# victory, over the api_server routes the generated CMD serves.
SID="smoke-$(date +%s)"
echo
echo "Smoke-testing $URL (session $SID) ..."
CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$URL/apps/demo_agent/users/u1/sessions/$SID" \
        -H 'content-type: application/json' \
        -d '{}')
[[ "$CODE" == "200" ]] || fail "POST /apps/demo_agent/users/u1/sessions/$SID returned $CODE."

CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$URL/run" \
        -H 'content-type: application/json' \
        -d '{"app_name":"demo_agent","user_id":"u1","session_id":"'"$SID"'",
             "new_message":{"role":"user","parts":[{"text":"What'\''s the weather in London?"}]}}')
[[ "$CODE" == "200" ]] || fail "POST /run returned $CODE."

cat <<EOF

Deployed and smoke-tested. Service URL: $URL

Send another turn (each one is a trace):
  SID=turn-\$(date +%s)
  curl -s -X POST "$URL/apps/demo_agent/users/u1/sessions/\$SID" \\
       -H 'content-type: application/json' -d '{}'
  curl -s -X POST "$URL/run" \\
       -H 'content-type: application/json' \\
       -d '{"app_name":"demo_agent","user_id":"u1","session_id":"'"\$SID"'",
            "new_message":{"role":"user","parts":[{"text":"What'\''s the weather in London?"}]}}'

Read the spans back from Cloud Trace (the v1 API takes a plain bearer token):
  curl -s -H "Authorization: Bearer \$(gcloud auth print-access-token)" \\
    "https://cloudtrace.googleapis.com/v1/projects/$PROJECT_ID/traces?startTime=$START_TS&orderBy=start%20desc&pageSize=3"

  # Then one whole trace, by the traceId from that list:
  curl -s -H "Authorization: Bearer \$(gcloud auth print-access-token)" \\
    "https://cloudtrace.googleapis.com/v1/projects/$PROJECT_ID/traces/TRACE_ID"

Read the same turn's content events back from Cloud Logging. On Cloud Run the
OTel exporter labels them with a generic_task resource whose job is the service
name (not a cloud_run_revision resource), so filter by the log name:
  gcloud logging read \\
    'logName:"gen_ai."' \\
    --project="$PROJECT_ID" \\
    --limit=10 \\
    --format=json \\
    --freshness=10m

Tear down:
  gcloud run services delete "$SERVICE" --project="$PROJECT_ID" --region="$REGION" --quiet
EOF
