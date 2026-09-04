# Container for the custom server (examples/06_custom_server.py).
# Cloud Run ingests stdout/stderr into Cloud Logging automatically, so the
# server's job is simply to write good JSON lines to stdout, which 06 does.

FROM python:3.13-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent, the plugin (05), and the server (06).
COPY demo_agent/ ./demo_agent/
COPY examples/_common.py ./examples/
COPY examples/05_structured_plugin.py ./examples/
COPY examples/06_custom_server.py ./examples/

# Cloud Run sets PORT; the server reads it. Bind to 0.0.0.0.
ENV PORT=8080
EXPOSE 8080

# No .env in the image: on Cloud Run, set GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION
# and GOOGLE_GENAI_USE_VERTEXAI via --set-env-vars at deploy time (see deploy_cloudrun.sh).
CMD ["python", "examples/06_custom_server.py"]
