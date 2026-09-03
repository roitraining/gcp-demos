# Custom container for Agent Runtime (tutorial 1.7). Serves the two runtime
# contract endpoints on $PORT (8080 on Agent Runtime). Agent Runtime ingests the
# container's stdout/stderr into Cloud Logging under reasoning_engine_stdout.

FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY demo_agent/ ./demo_agent/
COPY main.py .

ENV PORT=8080
EXPOSE 8080

# LOG_LEVEL and the Vertex config are set on the deployment's env (deploy_byoc.py).
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
