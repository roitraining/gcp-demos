# Container for the streamlined custom server (examples/07_cloudrun_json.py).
# Cloud Run ingests stdout/stderr into Cloud Logging automatically, so the
# server's job is simply to write good JSON lines to stdout, which 07 does.

FROM python:3.13-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent and the server.
COPY demo_agent/ ./demo_agent/
COPY examples/_common.py ./examples/
COPY examples/05_structured_plugin.py ./examples/
COPY examples/07_cloudrun_json.py ./examples/

# Cloud Run sets PORT; the server reads it. Bind to 0.0.0.0.
ENV PORT=8080
EXPOSE 8080

# No .env in the image: on Cloud Run, set GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION
# and GOOGLE_GENAI_USE_VERTEXAI via --set-env-vars at deploy time (see deploy_cloudrun.sh).
CMD ["python", "examples/07_cloudrun_json.py"]
