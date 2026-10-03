#!/usr/bin/env bash
#
# Tutorial 1.6: deploy the agent to Vertex AI Agent Engine (Agent Runtime),
# natively (you deploy the AGENT, not a web server; the platform hosts the
# runner). Telemetry is exported to Cloud Trace and Cloud Logging. OPTIONAL.
#
# Log level: on a native deploy there is no server script of ours to set the
# level, so demo_agent/agent.py reads it from the LOG_LEVEL env var. `adk deploy
# agent_engine` has no env-var flag; it carries the agent directory's .env into
# the deployed agent, so this script temporarily writes LOG_LEVEL into
# demo_agent/.env for the deploy and restores the original afterward, so the
# deploy value does not leak into local `adk web` runs.
#
# Two telemetry routes (tutorial 6.2 / 6.3):
#   default            — pass --otel_to_cloud. The CLI writes
#                        GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true AND
#                        ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false for you.
#   ENABLE_VIA_ENV=1   — no flag. This script writes the telemetry env var and
#                        BOTH content knobs into the temporary .env itself. The
#                        CLI still adds --otel_to_cloud to the server command,
#                        but sets no content knobs. Shows the .env route where
#                        you must set the knobs yourself.
#
# Usage:
#   export PROJECT_ID=your-project
#   export REGION=us-central1
#   ./deploy/deploy_agent_engine.sh                 # flag route (6.2)
#   ENABLE_VIA_ENV=1 ./deploy/deploy_agent_engine.sh # .env route (6.3)
#   LOG_LEVEL=warning ./deploy/deploy_agent_engine.sh
#
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-us-central1}"
LOG_LEVEL="${LOG_LEVEL:-info}"
MODEL_LOCATION="${MODEL_LOCATION:-global}"
ENABLE_VIA_ENV="${ENABLE_VIA_ENV:-0}"

# Save the original .env and restore it after deploy (success or failure), so
# LOG_LEVEL does not leak into local runs like `adk web`. If there was no
# demo_agent/.env, remove the one we write: ADK uses the first .env it finds
# walking up from the agent folder, so a leftover file would hide the root .env.
_HAD_ENV=""
[[ -f ./demo_agent/.env ]] && _HAD_ENV=1
_ORIG_ENV="$(cat ./demo_agent/.env 2>/dev/null || true)"
trap 'if [[ -n "$_HAD_ENV" ]]; then printf "%s\n" "$_ORIG_ENV" > ./demo_agent/.env; else rm -f ./demo_agent/.env; fi' EXIT

# Write the env the deployed agent needs. `adk deploy agent_engine` copies the
# agent directory's .env into the deployment.
cat > ./demo_agent/.env <<ENV
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=${PROJECT_ID}
GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION}
LOG_LEVEL=${LOG_LEVEL}
ENV

if [[ "$ENABLE_VIA_ENV" == "1" ]]; then
  # The .env route (6.3): turn telemetry on and set BOTH content knobs to their
  # safe values ourselves, since the CLI sets nothing without the flag. Then
  # deploy with NO --otel_to_cloud.
  cat >> ./demo_agent/.env <<ENV
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT
ENV
  echo "ENABLE_VIA_ENV=1: telemetry + both content knobs written into .env; deploying WITHOUT --otel_to_cloud." >&2
  # No flag. (bash 3.2 on macOS errors on empty-array expansion under set -u,
  # so branch the whole command rather than splat a possibly-empty flag array.)
  _DEPLOY_OUT="$(./.venv/bin/adk deploy agent_engine \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --display_name="adk-logging-demo" \
    ./demo_agent 2>&1 | tee /dev/stderr)"
else
  # The flag route (6.2): --otel_to_cloud sets the telemetry var and the span
  # knob (ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false) for you.
  _DEPLOY_OUT="$(./.venv/bin/adk deploy agent_engine \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --display_name="adk-logging-demo" \
    --otel_to_cloud \
    ./demo_agent 2>&1 | tee /dev/stderr)"
fi

# Extract the reasoning engine resource name that adk prints, e.g.
# projects/P/locations/R/reasoningEngines/1234567890. Last match wins.
ENGINE_RESOURCE="$(printf '%s\n' "$_DEPLOY_OUT" \
  | grep -oE 'projects/[^ "]+/locations/[^ "]+/reasoningEngines/[0-9]+' \
  | tail -n1)"
ENGINE_ID="${ENGINE_RESOURCE##*/}"

cat <<EOF

Deployed to Agent Engine. What differs from Cloud Run for logging:

  * You do not write the server: the CLI generated a container that runs
    'adk api_server'. The platform captures its stdout and stderr.
  * Logs land against the monitored resource:
        aiplatform.googleapis.com/ReasoningEngine
    but the agent/framework log lines are on the STDERR log, not stdout:
        aiplatform.googleapis.com/reasoning_engine_stderr
    (reasoning_engine_stdout carries only the uvicorn access lines). The
    platform installs its OWN logging handler, so your log FORMAT is the ADK
    CLI's timestamped "file:line" format, not your basicConfig format; a
    basicConfig(format=...) in the agent module is overridden.
  * Telemetry is switched by GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY on the
    deployment. --otel_to_cloud wrote it to "true" and put --otel_to_cloud on
    the server's start command; a line in the agent's .env does the same on a
    plain 'adk deploy agent_engine' (Part 6 shows the .env route). Set neither
    and the platform decides. Do not rely on that.

Read the agent logs — note it is the STDERR log, and use the resource filter so
you catch both streams:

  gcloud logging read \\
    'resource.type="aiplatform.googleapis.com/ReasoningEngine" resource.labels.reasoning_engine_id="\${ENGINE_ID}"' \\
    --project="$PROJECT_ID" --limit=30 --format='table(severity,textPayload)'
EOF

# Machine-readable marker on the LAST stdout line (the progress above went to
# stderr via tee), so a caller can capture the bare engine id with:
#   export ENGINE_NATIVE=$(./deploy/deploy_agent_engine.sh | sed -n 's/^ENGINE_ID=//p')
printf 'ENGINE_ID=%s\n' "$ENGINE_ID"
