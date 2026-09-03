#!/usr/bin/env bash
#
# Tutorial 1.6: deploy the agent to Vertex AI Agent Engine (Agent Runtime),
# natively (you deploy the AGENT, not a web server; the platform hosts the
# runner). Telemetry is exported to Cloud Trace and Cloud Logging. OPTIONAL.
#
# Log level: on a native deploy there is no server script of ours to set the
# level, so demo_agent/agent.py reads it from the LOG_LEVEL env var. `adk deploy
# agent_engine` has no env-var flag; it carries the agent directory's .env into
# the deployed agent, so this script writes LOG_LEVEL into demo_agent/.env (plus
# the Vertex config the agent needs) before deploying.
#
# Usage:
#   export PROJECT_ID=your-project
#   export REGION=us-central1
#   ./deploy/deploy_agent_engine.sh                 # deploy at LOG_LEVEL=info
#   LOG_LEVEL=warning ./deploy/deploy_agent_engine.sh
#
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-us-central1}"
LOG_LEVEL="${LOG_LEVEL:-info}"
MODEL_LOCATION="${MODEL_LOCATION:-global}"

# Write the env the deployed agent needs. `adk deploy agent_engine` copies the
# agent directory's .env into the deployment.
cat > ./demo_agent/.env <<ENV
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=${PROJECT_ID}
GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION}
LOG_LEVEL=${LOG_LEVEL}
ENV

# --otel_to_cloud turns on telemetry export; under the hood it sets
# GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true on the deployed agent.
adk deploy agent_engine \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --display_name="adk-logging-demo" \
  --otel_to_cloud \
  ./demo_agent

cat <<EOF

Deployed to Agent Engine. What differs from Cloud Run for logging:

  * You do not run uvicorn or write JSON lines yourself. The platform captures
    stdout and the ADK OTel signals.
  * Logs land against the monitored resource:
        aiplatform.googleapis.com/ReasoningEngine
    but the agent/framework log lines are on the STDERR log, not stdout:
        aiplatform.googleapis.com/reasoning_engine_stderr
    (reasoning_engine_stdout carries only the uvicorn access lines). The
    platform installs its OWN logging handler, so your log FORMAT is the ADK
    CLI's timestamped "file:line" format, not your basicConfig format; a
    basicConfig(format=...) in the agent module is overridden.
  * Traces appear in Cloud Trace automatically (no --otel_to_cloud needed for
    traces on Agent Engine; the flag additionally routes logs and metrics).

Read the agent logs (replace ENGINE_ID with the reasoning engine id printed
above) — note it is the STDERR log, and use the resource filter so you catch
both streams:

  gcloud logging read \\
    'resource.type="aiplatform.googleapis.com/ReasoningEngine" resource.labels.reasoning_engine_id="ENGINE_ID"' \\
    --project="$PROJECT_ID" --limit=30 --format='table(severity,textPayload)'
EOF
