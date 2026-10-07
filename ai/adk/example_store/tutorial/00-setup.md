[→ Part 1 · The agent without examples](part-1/index.md)<br>
[Tutorial index](../TUTORIAL.md)

---

# Setup

All commands run from `ai/adk/example_store`. Do this once. The last step
starts the Example Store, which takes about 8 to 9 minutes to create, so you start
it here and do Part 1 while it builds.

## Create the environment

From the repo root:

**Command:**

```bash
cd ai/adk/example_store
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Point the agent at a project

Copy the example settings file:

**Command:**

```bash
cp .env.example .env
```

Open `.env` in your editor and set `GOOGLE_CLOUD_PROJECT` to your project ID.
Leave `EXAMPLE_STORE_NAME` empty for now; the last step fills it in.

```
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
EXAMPLE_STORE_NAME=
```

`GOOGLE_CLOUD_LOCATION=global` is where the agent calls Gemini. The store
itself lives in `us-central1`, which [store/_common.py](../store/_common.py)
sets for the store scripts.

If you have not authenticated before, log in once:

**Command:**

```bash
gcloud auth application-default login
```

## Enable the API

Example Store, Gemini, and the embedding model all sit behind the Vertex AI
API. Set your project ID in the shell, then enable the API:

**Command:**

```bash
export PROJECT_ID=your-project-id
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
```

## Start creating the store

Open a second terminal in `ai/adk/example_store` and run:

**Command:**

```bash
.venv/bin/python store/create_store.py
```

**Expected output:** progress lines, then about 8 minutes later the line to copy. Your IDs differ.

```console
Creating ExampleStore
Create ExampleStore backing LRO: projects/240659336105/locations/us-central1/exampleStores/1983052783577726976/operations/8740305713475092480
ExampleStore created. Resource name: projects/240659336105/locations/us-central1/exampleStores/1983052783577726976
To use this ExampleStore in another session:
example_store = aiplatform.ExampleStore('projects/240659336105/locations/us-central1/exampleStores/1983052783577726976')

EXAMPLE_STORE_NAME=projects/240659336105/locations/us-central1/exampleStores/1983052783577726976
```

Leave it running and go to Part 1. When it finishes, copy the
`EXAMPLE_STORE_NAME=...` line into `.env`, replacing the empty one. Part 2
reads it.

> [!NOTE]
> **The store stays until you delete it.** The last step of
> [3.2](part-3/3.2-when-retrieval-runs.md) deletes it.

---

[→ Part 1 · The agent without examples](part-1/index.md)<br>
[Tutorial index](../TUTORIAL.md)
