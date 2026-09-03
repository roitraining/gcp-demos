# Runbook: capture output for tutorial 1.4–1.7

Run these four, collect the output blocks marked **COLLECT**, and paste them
back. Each section's prose gets written from the real output, so exact copies
matter more than tidy ones.

Common env (set once per shell):

```bash
export PROJECT_ID=jwd-gcp-demos
export REGION=us-central1
cd ~/Desktop/Dev/gcp-demos/ai/adk/logging
```

The big question 1.4 and 1.5 are testing: **does a plain `logging.basicConfig`
line (written to stderr) show up in Cloud Logging as ERROR severity, while the
`print()`ed answer (stdout) shows up as INFO/Default?** Watch the severity
column.

---

## 1.4 — plain script as a Cloud Run Job

### Deploy + run at INFO

```bash
./deploy/deploy_job.sh
```

This builds the image, deploys the job, and executes it once at `info`.

### Run again at WARNING (no rebuild needed)

```bash
gcloud run jobs execute adk-logging-job \
  --project="$PROJECT_ID" --region="$REGION" \
  --args=warning --wait
```

### COLLECT 1.4-A — the severity table

```bash
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-logging-job"' \
  --project="$PROJECT_ID" --limit=40 \
  --format='table(severity,textPayload)' --freshness=15m
```

### COLLECT 1.4-B — which execution each line came from

Lets us tell the INFO run apart from the WARNING run.

```bash
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-logging-job"' \
  --project="$PROJECT_ID" --limit=40 \
  --format='table(timestamp,severity,labels."run.googleapis.com/execution_name",textPayload)' \
  --freshness=15m
```

### COLLECT 1.4-C — raw JSON of 3 entries

Shows how each line was actually parsed (severity source, stream).

```bash
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-logging-job"' \
  --project="$PROJECT_ID" --limit=3 --format=json --freshness=15m
```

---

## 1.5 — minimal API server as a Cloud Run service

### Deploy at INFO

```bash
./deploy/deploy_api.sh
```

It deploys, then smoke-tests `/chat` itself and prints the service URL. Grab the
URL:

```bash
export API_URL=$(gcloud run services describe adk-logging-api \
  --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')
echo "$API_URL"
```

### COLLECT 1.5-A — a /chat request and its response

The service is `--allow-unauthenticated`, so no auth header is needed.

```bash
curl -s -X POST "$API_URL/chat" \
  -H 'content-type: application/json' \
  -d '{"message":"What'\''s the weather in Tokyo?"}'
echo
```

### COLLECT 1.5-B — the logs after that request (INFO)

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" resource.labels.service_name="adk-logging-api"' \
  --project="$PROJECT_ID" --limit=40 \
  --format='table(severity,textPayload)' --freshness=10m
```

Look for three kinds of line: your `agent.server` line, the `google_adk...`
framework lines, and uvicorn's `INFO: ... "POST /chat HTTP/1.1" 200 OK` access
line, plus the `demo_agent.agent` tool line.

### Redeploy at WARNING and repeat

```bash
LOG_LEVEL=warning ./deploy/deploy_api.sh
curl -s -X POST "$API_URL/chat" \
  -H 'content-type: application/json' \
  -d '{"message":"What'\''s the weather in Tokyo?"}'
echo
```

### COLLECT 1.5-C — the logs at WARNING

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" resource.labels.service_name="adk-logging-api"' \
  --project="$PROJECT_ID" --limit=40 \
  --format='table(severity,textPayload)' --freshness=5m
```

The question here: at WARNING, the framework/tool lines go quiet, but do the
uvicorn access lines keep printing? (They should — that is the Part 2 lesson,
now visible in the cloud.)

---

## 1.6 — native agent on Agent Runtime

### Deploy at INFO

```bash
./deploy/deploy_agent_engine.sh
```

This writes `demo_agent/.env` (with `LOG_LEVEL=info`) and runs
`adk deploy agent_engine`. **Watch the output for the reasoning engine id / full
resource name it prints** — you need it for the query and the log read.

### COLLECT 1.6-A — the deploy output

Paste the tail of the deploy, specifically the line with the resource name
(looks like `projects/.../locations/.../reasoningEngines/1234567890`).

Save the numeric id:

```bash
export ENGINE_ID=<the-number-at-the-end-of-the-resource-name>
```

### COLLECT 1.6-B — one query

`adk deploy` catches failures and still exits 0, so this query is the real test
that it works. Query via the SDK (the raw `:streamQuery` REST URL 404s; the SDK
builds the correct path and handles auth):

```bash
.venv/bin/python - <<PY
import vertexai
c = vertexai.Client(project="$PROJECT_ID", location="$REGION")
name = "projects/$PROJECT_ID/locations/$REGION/reasoningEngines/$ENGINE_ID"
agent = c.agent_engines.get(name=name)
for ev in agent.stream_query(user_id="u1", message="What's the weather in Tokyo?"):
    for part in ((ev or {}).get("content") or {}).get("parts", []):
        if part.get("text"):
            print(part["text"])
PY
```

Note: `$PROJECT_ID` in the resource name works, but the resource name the
platform actually uses has the project NUMBER; the SDK resolves either.

### COLLECT 1.6-C — the logs

Read by RESOURCE, not by log name: the agent/framework lines are on the
`reasoning_engine_stderr` log, while `reasoning_engine_stdout` only has the
uvicorn access lines. Filtering on `resource.type` catches both.

```bash
gcloud logging read \
  "resource.type=\"aiplatform.googleapis.com/ReasoningEngine\" resource.labels.reasoning_engine_id=\"$ENGINE_ID\"" \
  --project="$PROJECT_ID" --limit=30 \
  --format='table(severity,textPayload)' --freshness=15m
```

Note what to look for: the tool line arrives as
`... - INFO - agent.py:53 - tool get_weather called ...` — the ADK CLI's
timestamped `file:line` format, NOT our `basicConfig` format. The platform
installs its own logging handler.

### Redeploy at WARNING and re-test the level dial

The format is the platform's, but does our `LOG_LEVEL` still filter? At INFO the
`google_adk` / tool lines are present; at WARNING they should disappear if our
`setLevel` calls took effect. This redeploys the same agent with
`LOG_LEVEL=warning` in its `.env`.

```bash
LOG_LEVEL=warning ./deploy/deploy_agent_engine.sh
```

**Grab the NEW engine id** from the deploy output — a redeploy of a native agent
via `adk deploy agent_engine` creates a new reasoning engine, it does not update
the old one in place:

```bash
export ENGINE_ID_W=<the-number-at-the-end-of-the-NEW-resource-name>
```

### COLLECT 1.6-D — one query against the WARNING engine

```bash
.venv/bin/python - <<PY
import vertexai
c = vertexai.Client(project="$PROJECT_ID", location="$REGION")
name = "projects/$PROJECT_ID/locations/$REGION/reasoningEngines/$ENGINE_ID_W"
agent = c.agent_engines.get(name=name)
for ev in agent.stream_query(user_id="u1", message="What's the weather in Tokyo?"):
    for part in ((ev or {}).get("content") or {}).get("parts", []):
        if part.get("text"):
            print(part["text"])
PY
```

### COLLECT 1.6-E — the WARNING engine's logs

```bash
gcloud logging read \
  "resource.type=\"aiplatform.googleapis.com/ReasoningEngine\" resource.labels.reasoning_engine_id=\"$ENGINE_ID_W\"" \
  --project="$PROJECT_ID" --limit=30 \
  --format='table(severity,textPayload)' --freshness=15m
```

The question: are the `google_adk` / `agent.py` tool lines GONE (our `setLevel`
worked through the platform's handler) or STILL THERE (the platform's level wins
and ignores ours)? Either answer is a real finding for the tutorial. Paste the
table.

> Two engines now exist (INFO `$ENGINE_ID`, WARNING `$ENGINE_ID_W`). Delete the
> INFO one once you have both captures if you want to keep the project tidy; the
> teardown section deletes both.

---

## 1.7 — custom container on Agent Runtime (BYOC)

### Deploy at INFO

```bash
cd ~/Desktop/Dev/gcp-demos/ai/adk/logging/agent_runtime_byoc
export PROJECT_ID=jwd-gcp-demos
export LOCATION=us-central1
./deploy_byoc.sh
```

This creates an Artifact Registry repo (if missing), builds/pushes the image,
and registers the container as an Agent Runtime instance. It prints the full
resource name at the end.

### COLLECT 1.7-A — the deploy output

Paste the tail, especially the `Reasoning engine resource:` line. Save it:

```bash
export BYOC_RESOURCE=<the-full-projects/.../reasoningEngines/... name>
export BYOC_ENGINE_ID=<the-number-at-the-end>
```

### COLLECT 1.7-B — query through the /api passthrough

Note the doubled `/api/api/` — the passthrough prefix plus the container's own
`/api` route. This is the part most likely to need adjusting against reality; if
it 404s or errors, paste the full response and I will fix the URL.

```bash
curl -s -X POST \
  "https://$LOCATION-aiplatform.googleapis.com/reasoningEngines/v1/$BYOC_RESOURCE/api/api/stream_reasoning_engine" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H 'content-type: application/json' \
  -d '{"class_method":"async_stream_query","input":{"user_id":"u1","message":"What'\''s the weather in Tokyo?"}}'
echo
```

### COLLECT 1.7-C — the logs

```bash
gcloud logging read \
  "logName:\"reasoning_engine_stdout\" resource.labels.reasoning_engine_id=\"$BYOC_ENGINE_ID\"" \
  --project="$PROJECT_ID" --limit=30 \
  --format='table(severity,textPayload)' --freshness=15m
```

Same question as 1.6: do our naive Part 1 lines (`INFO - name - message`, the
tool line) show up, and at what severity?

---

## Teardown (after we have the output)

```bash
# 1.4 job
gcloud run jobs delete adk-logging-job --project="$PROJECT_ID" --region="$REGION" --quiet

# 1.5 service
gcloud run services delete adk-logging-api --project="$PROJECT_ID" --region="$REGION" --quiet

# 1.6 native agent (ENGINE_ID from 1.6-A)
python -c "import vertexai; vertexai.Client(project='$PROJECT_ID', location='$REGION').agent_engines.delete(name='projects/$PROJECT_ID/locations/$REGION/reasoningEngines/$ENGINE_ID', force=True)"

# 1.7 BYOC container (BYOC_RESOURCE from 1.7-A)
python -c "import vertexai; vertexai.Client(project='$PROJECT_ID', location='$LOCATION').agent_engines.delete(name='$BYOC_RESOURCE', force=True)"
```

Hold teardown until the tutorial sections are written, in case we need a second
capture.
