# Shopping List API server

Silly little demo API that returns a generated shopping list (JSON). The service
calls Vertex AI's GenAI (Gemini) via the `google-genai` SDK and exposes a single
HTTP GET endpoint that returns a list of items suitable for demo/testing.

## What this does

- Starts a FastAPI server (listens on port 8080 by default).
- Calls a Gemini model to generate a small shopping list in JSON.
- Returns the list as: `{ "items": [ {"name":..., "quantity":..., "aisle":...}, ... ] }`.

## Files of interest

- `main.py` - FastAPI app and GenAI client usage.
- `pyproject.toml` - project metadata and dependencies.
- `Dockerfile` - container image build for running the app in Docker.

## Prerequisites

- Python 3.12 (the project `pyproject.toml` requests >=3.12) or Docker.
- A Google Cloud project with Vertex AI enabled and a service account that has
  permission to call Vertex AI.
- The `GOOGLE_CLOUD_PROJECT` environment variable must be set.

Optional but recommended environment variables in a `.env` file:

```
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

If running locally, authenticate with `gcloud auth application-default login`
or set `GOOGLE_APPLICATION_CREDENTIALS` to a service account JSON key.

## Run with Docker (recommended)

Build the image from the `shopping_list_api` directory and run it:

```bash
docker build -t shopping-list-api .
docker run -p 8080:8080 \
  -e GOOGLE_CLOUD_PROJECT=your-gcp-project-id \
  -e GOOGLE_CLOUD_LOCATION=us-central1 \
  shopping-list-api
```

The server will be reachable at `http://localhost:8080`.

## Run locally (development)

1. Export env vars (or create a `.env` file) and run:

```bash
export GOOGLE_CLOUD_PROJECT=your-gcp-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
uv run uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## API

GET /get-list

- Description: Generates a Costco-style shopping list using Gemini and returns
  it as JSON.
- Response schema:

```json
{
  "items": [
    {"name": "string", "quantity": 1, "aisle": "string"}
  ]
}
```

Example curl:

```bash
curl -s http://localhost:8080/get-list | jq
```

Expected behaviors and error cases:

- If the GenAI call fails, the server returns HTTP 500 with a message.
- If the model returns non-JSON or invalid JSON, the server returns HTTP 500.

## Environment / Authentication notes

- When deployed on GCE/GKE/Cloud Run with the correct service account, the app
  will use Workload Identity / service account credentials automatically.
- For local testing, set `GOOGLE_APPLICATION_CREDENTIALS` to a service account
  key file that has permission to call Vertex AI, or run
  `gcloud auth application-default login`.
