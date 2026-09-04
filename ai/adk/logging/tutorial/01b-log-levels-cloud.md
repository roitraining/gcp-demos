# Part 1 · The log level, in the cloud

*The same run on a Cloud Run Job and service, and on Agent Runtime — native and
BYOC. Sections 1.1–1.3 (on your laptop) are in the [previous file](01a-log-levels-local.md).*

### 1.4 The same script on Cloud Run, and what Cloud Logging does to it

> [!NOTE]
> **Why you are here.** So far every run was on your laptop, where a log line is
> just text on your terminal. The moment you deploy, a second system gets an
> opinion about your logs: Cloud Logging reads each line, assigns it a
> **severity**, and files it under a stream. Before you write a single line of
> cloud-specific logging (Part 6 does that), you should see what Cloud Logging
> makes of the *unmodified* Part 1 script, because the answer is not what the
> common advice says.

The script from 1.1 runs once and exits; it serves no HTTP. The right way to
run it on Cloud Run is a **Job**, not a service (a service would fail
its readiness check with no port to probe). A Job runs the container to
completion, and Cloud Run ingests its stdout and stderr into Cloud Logging
automatically. [deploy/deploy_job.sh](../deploy/deploy_job.sh) builds the image,
deploys the Job, and runs it once; the level is a Job argument, so you can
re-run at a different level without rebuilding.

**👉 Do this.** Deploy and run at INFO, then run again at WARNING:

```bash
export PROJECT_ID=your-project REGION=us-central1
./deploy/deploy_job.sh                 # deploys, then executes at info
gcloud run jobs execute adk-logging-job \
  --project="$PROJECT_ID" --region="$REGION" --args=warning --wait
```

Then read the two runs back, asking for the severity of each line:

```bash
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-logging-job"' \
  --project="$PROJECT_ID" --limit=40 \
  --format='table(severity,textPayload)' --freshness=15m
```

**You will see** the INFO execution carry the full lifecycle and the WARNING
execution carry almost nothing (trimmed, most recent first):

```console
SEVERITY  TEXT_PAYLOAD
          ===== running at WARNING =====
          >>> ANSWER: The weather in Tokyo is currently 27°C and humid.
INFO      Container called exit(0).
          ===== running at INFO =====
          INFO - google_adk.google.adk.models.google_llm - Sending out request, model: gemini-3.7-flash, backend: GoogleLLMVariant.VERTEX_AI, stream: False
          INFO - demo_agent.agent - tool get_weather called for city='Tokyo'
          INFO - google_adk.google.adk.models.google_llm - Response received from the model.
          >>> ANSWER: The weather in Tokyo is currently 27°C and humid.
INFO      Container called exit(0).
```

> [!TIP]
> **What it means, finding one: the level dial works in the cloud, unchanged.**
> The WARNING execution shows the banner and the answer and *no* `google_adk` or
> tool lines; the INFO execution shows the whole five-line lifecycle you know from
> 1.1.1. Nothing about deploying changed what the level controls. This is the
> reassuring half.

> [!TIP]
> **What it means, finding two: severity is not what you were told.** There is a
> rule repeated all over the Cloud Run docs and even in ADK's own source comments:
> *a line written to stderr is recorded as ERROR severity regardless of content.*
> `logging.basicConfig` writes to stderr, so by that rule every `INFO -
> google_adk...` line above should read as ERROR. Look at the severity column: it
> does not. Those lines came through with **blank (Default) severity, not ERROR**.
> You can confirm they really are on stderr:

```bash
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-logging-job"
   textPayload:"get_weather"' \
  --project="$PROJECT_ID" --limit=1 --format='value(logName,textPayload)' --freshness=15m
# projects/.../logs/run.googleapis.com%2Fstderr  INFO - demo_agent.agent - tool get_weather called ...
```

The line is on stderr (`.../logs/run.googleapis.com%2Fstderr`), and its severity
is still Default, not ERROR. The often-repeated "stderr means ERROR" rule did not
fire here. (It is real in some contexts, but it is not the blanket law it is
usually stated as; 1.5 finds the same Default-not-ERROR result on a Cloud Run
*service*.) So **do not assume the severity of a plain line, check it**: Cloud
Run's guess is not reliably what you want.

So the zero-effort deploy gets you two-thirds of the way. Your logs reach Cloud
Logging, and the level still filters them. What you do *not* get is **correct,
queryable severity**: every one of these `INFO -` lines is filed as Default, so a
severity-based query or alert cannot tell an error from a routine step. Making
severity a field you set, not a guess Cloud Run makes from the stream, is the job
of Part 6.

> [!NOTE]
> One display note: Cloud Run batches burst console output, so several of the
> script's lines can arrive grouped under one Cloud Logging entry (you will see
> the `===== running =====` banner and the lifecycle lines share an entry
> above). That is a grouping artifact of the read, not a change to your logs.

### 1.5 The same logging behind a real HTTP server

> [!NOTE]
> **Why you are here.** A Job runs once and exits. A real service stays up and
> takes requests, which adds the one stream a script never has: the web server's
> own access log (stream 3 from the introduction). This section deploys the
> smallest possible ADK HTTP server, one that does *nothing* special about
> logging, so you can see all of Part 1's streams land in Cloud Logging together,
> and confirm on a long-running service what 1.4 found on a Job.

[examples/09_min_api.py](../examples/09_min_api.py) is that server. It is
deliberately naive: it configures logging with the exact `configure(level)` from
1.1 (a level plus `logging.basicConfig`), reads the level from a `LOG_LEVEL`
environment variable, and starts uvicorn **without** a log config, so uvicorn's
own default access logging is left untouched. It exposes one real route,
`POST /chat`, and a `GET /healthz`. That is the whole server. (Contrast it with
the servers in Parts 5 and 6, which take control of every stream; this one takes
control of none, on purpose.)

**👉 Do this.** Deploy it (unauthenticated, for demo simplicity), then send the same
Tokyo question:

```bash
export PROJECT_ID=your-project REGION=us-central1
./deploy/deploy_api.sh                 # deploys at LOG_LEVEL=info
API_URL=$(gcloud run services describe adk-logging-api \
  --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')

curl -s -X POST "$API_URL/chat" -H 'content-type: application/json' \
     -d '{"message":"What'\''s the weather in Tokyo?"}'
```

```json
{"response":"The weather in Tokyo is currently 27°C and humid."}
```

Now read the logs:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" resource.labels.service_name="adk-logging-api"' \
  --project="$PROJECT_ID" --limit=40 \
  --format='table(severity,textPayload)' --freshness=10m
```

**You will see** all of Part 1's streams in one place (trimmed):

```console
SEVERITY  TEXT_PAYLOAD
          INFO - agent.server - runner ready
          INFO:     Started server process [1]
          INFO:     Application startup complete.
          INFO - google_adk.google.adk.models.google_llm - Sending out request, model: gemini-3.7-flash, backend: GoogleLLMVariant.VERTEX_AI, stream: False
          INFO - demo_agent.agent - tool get_weather called for city='Tokyo'
          INFO - google_adk.google.adk.models.google_llm - Response received from the model.
          INFO:     169.254.169.126:2186 - "POST /chat HTTP/1.1" 200 OK
```

> [!TIP]
> **What it means.** Four sources, interleaved, exactly as they were on your
> laptop: your server's own `agent.server` line, the `google_adk` framework lines,
> your tool's `demo_agent.agent` line, and, new for a server, uvicorn's
> `INFO: ... "POST /chat HTTP/1.1" 200 OK` access line. Nothing here is
> cloud-shaped; it is the raw Part 1 output, now arriving from a container.

And the severity column repeats 1.4's finding on a service: every `INFO -` line
is filed as **Default, not ERROR**, even though `basicConfig` writes them to
stderr. So the folklore does not hold on a Cloud Run service either. Two kinds of
line *do* carry a real severity, and neither is your application's:

- `INFO` on the `Starting new instance` / `STARTUP TCP probe` lines: those are
  Cloud Run's own platform logs, which it labels correctly.
- `WARNING` on some rows with blank text: those are Cloud Run's built-in
  **request log** (`run.googleapis.com/requests`), one per HTTP request, marked
  WARNING here because the requests were `404`s (a browser hitting `/` and
  `/favicon.ico`). That log is separate from uvicorn's access line and from your
  app entirely.

**Now turn the level down and watch the split.** Redeploy at WARNING and send the
same request again:

```bash
LOG_LEVEL=warning ./deploy/deploy_api.sh
curl -s -X POST "$API_URL/chat" -H 'content-type: application/json' \
     -d '{"message":"What'\''s the weather in Tokyo?"}'
gcloud logging read \
  'resource.type="cloud_run_revision" resource.labels.service_name="adk-logging-api"' \
  --project="$PROJECT_ID" --limit=40 \
  --format='table(severity,textPayload)' --freshness=5m
```

**You will see** the framework and tool lines gone, and the access line still
there:

```console
SEVERITY  TEXT_PAYLOAD
          INFO:     169.254.169.126:37574 - "POST /chat HTTP/1.1" 200 OK
WARNING
          INFO:     169.254.169.126:37562 - "GET /favicon.ico HTTP/1.1" 404 Not Found
```

> [!TIP]
> **What it means.** `LOG_LEVEL=warning` reached streams 1 and 2 (your code and
> `google_adk`), which is why the lifecycle lines vanished, exactly as 1.1.3 taught
> you. It did **not** reach uvicorn's access log: the `"POST /chat" 200 OK` line
> prints regardless, because that stream is configured by uvicorn, not by your
> level. That is the whole of Part 2, now visible in the cloud: on a busy service
> this is one access line per request forever, health checks included, no matter
> how far down you turn your level. Part 2 fixes it; Part 6 makes the rest of these
> lines into structured entries with severity you can query.

> [!NOTE]
> If, right after a WARNING redeploy, you still see a few `google_adk` lines,
> they are from the previous INFO revision still inside the read's freshness
> window (you will see `Reason: DEPLOYMENT_ROLLOUT` entries marking the switch).
> Wait for the old revision to drain, or narrow `--freshness`.

### 1.6 The same agent on Agent Runtime, where the platform logs for you

> [!NOTE]
> **Why you are here.** Cloud Run (1.4, 1.5) gave you a container and got out of
> the way: whatever you wrote to stdout/stderr is what you got. Agent Runtime
> (Vertex AI Agent Engine) is the other place you deploy, and it is different in a
> way that matters for logging: you deploy the **agent**, not a web server, and the
> platform runs it for you. That means the platform, not your code, decides how
> your logs are handled. This section shows exactly which parts of Part 1 you still
> control there, and which the platform takes over.

You deploy with `adk deploy agent_engine`, which packages the agent directory and
hands it to the platform. There is no server of yours in the picture, so there is
no `uvicorn.run` and no `configure()` call at a `__main__`. The one hook you have
for the log level is an environment variable: `demo_agent/agent.py` reads
`LOG_LEVEL` at import and applies it (this tutorial added that). `adk deploy
agent_engine` has no env flag, but it carries the agent directory's `.env` into
the deployment, so [deploy/deploy_agent_engine.sh](../deploy/deploy_agent_engine.sh)
writes `LOG_LEVEL` there before deploying.

**👉 Do this.** Deploy at INFO, note the reasoning engine id it prints, and send one
query. The query goes through the SDK (the platform's query path is not a plain
REST URL you can curl):

```bash
export PROJECT_ID=your-project REGION=us-central1
./deploy/deploy_agent_engine.sh                 # writes LOG_LEVEL=info, deploys
export ENGINE_ID=<the number at the end of the resource name it printed>

.venv/bin/python - <<PY
import vertexai
c = vertexai.Client(project="$PROJECT_ID", location="$REGION")
agent = c.agent_engines.get(
    name="projects/$PROJECT_ID/locations/$REGION/reasoningEngines/$ENGINE_ID")
for ev in agent.stream_query(user_id="u1", message="What's the weather in Tokyo?"):
    for part in ((ev or {}).get("content") or {}).get("parts", []):
        if part.get("text"):
            print(part["text"])
PY
# -> The weather in Tokyo is currently 27°C and humid.
```

Then read the logs. Read by **resource**, not by log name: the agent and
framework lines land on the `reasoning_engine_stderr` log, while
`reasoning_engine_stdout` carries only the web server's access lines. Filtering on
`resource.type` catches both.

```bash
gcloud logging read \
  'resource.type="aiplatform.googleapis.com/ReasoningEngine"
   resource.labels.reasoning_engine_id="'"$ENGINE_ID"'"' \
  --project="$PROJECT_ID" --limit=30 \
  --format='table(severity,textPayload)' --freshness=15m
```

**You will see** the familiar lifecycle, but not in your format:

```console
SEVERITY  TEXT_PAYLOAD
          2026-09-03 21:51:43,236 - INFO - google_llm.py:255 - Sending out request, model: gemini-3.7-flash, backend: GoogleLLMVariant.VERTEX_AI, stream: False
          2026-09-03 21:51:45,037 - INFO - agent.py:53 - tool get_weather called for city='Tokyo'
          2026-09-03 21:51:46,995 - INFO - google_llm.py:327 - Response received from the model.
          INFO:     169.254.169.126:54632 - "POST /api/stream_reasoning_engine HTTP/1.1" 200 OK
```

> [!TIP]
> **What it means: the platform owns your log format and stream, you keep the
> level.** Compare that tool line to 1.5. On Cloud Run it read
> `INFO - demo_agent.agent - tool get_weather...`, your `basicConfig` format. Here
> it reads `2026-09-03 21:51:45,037 - INFO - agent.py:53 - tool get_weather...`,
> the ADK CLI's timestamped `file:line` format, the same one you saw from
> `adk api_server` back in 1.3. Your `basicConfig(format=...)` did not take: the
> platform installs its own logging handler before your module runs, so it decides
> the format and the destination (stderr), and your handler config is ignored.

What you *do* still control is the **level**, because setting a logger's level
works regardless of who owns the handler. Redeploy at WARNING and send the same
query:

```bash
LOG_LEVEL=warning ./deploy/deploy_agent_engine.sh
export ENGINE_ID_W=<the NEW number; a redeploy creates a new engine>
# ...query it the same way, then read its logs...
```

**You will see** the framework and tool lines gone:

```console
SEVERITY  TEXT_PAYLOAD
          INFO:     169.254.169.126:14600 - "POST /api/stream_reasoning_engine HTTP/1.1" 200 OK
          2026-09-03 22:03:22,566 - INFO - envs.py:83 - Loaded .env file for demo_agent
```

No `google_llm` request line, no `tool get_weather` line: the same run, silenced
by level, exactly as it was on Cloud Run and on your laptop. The scorecard for
native Agent Runtime is: **level, yours** (via `LOG_LEVEL`); **format, stream, and
severity, the platform's.** Severity is blank/Default here too, the same
limitation as Cloud Run, and the same reason Part 6 exists.

This decides what carries over from Part 4. The structured plugin you build
there still works here: its records go through whatever handler the platform
installed, and its `extra=` fields survive. Any formatting you try to impose
from your own `dictConfig` does not.

> [!WARNING]
> Two traps. First, `adk deploy agent_engine` **creates a new reasoning engine on
> every deploy**; it does not update in place, so the WARNING redeploy has a new
> `ENGINE_ID`. Delete the old ones when you are done (the deploy script prints the
> teardown command). Second, `adk deploy` exits 0 even when the underlying deploy
> failed, so the query is the real success check, not the exit code.

### 1.7 The same server as a custom container on Agent Runtime

> [!NOTE]
> **Why you are here.** 1.6 deployed the agent object and let the platform serve it.
> But Agent Runtime also accepts a **container you build yourself** (bring your own
> container), which is how you run 1.5's kind of hand-written server on the managed
> platform instead of on Cloud Run. The catch is that the platform's contract
> constrains what that container must be.

A custom container on Agent Runtime is not free-form. The runtime contract
requires it to listen on **port 8080** and implement two specific routes,
`POST /api/reasoning_engine` (unary) and `POST /api/stream_reasoning_engine`
(streaming), each taking a `{"class_method", "input"}` body. A plain `/chat`
route like 1.5's is therefore not enough on its own. The smallest server that
satisfies the contract wraps the agent in `vertexai.agent_engines.AdkApp` and
dispatches the named method to it; that is what
[agent_runtime_byoc/main.py](../agent_runtime_byoc/main.py) does, in about ninety
lines. Its logging is deliberately the same naive Part 1 config as 1.5. This
section tests whether your own container gives you your logging format back, or
the platform overrides it the way it did in 1.6.

**👉 Do this.** Build, push, and register the container, then query it through the
platform's `/api` passthrough:

```bash
cd agent_runtime_byoc
export PROJECT_ID=your-project LOCATION=us-central1
./deploy_byoc.sh                 # builds, pushes, grants IAM, registers
```

The script prints the reasoning engine resource name. Query it with the same SDK
call as 1.6 (`stream_query`), then read its logs the same way (by
`resource.type`, at `reasoning_engine_stderr`).

**Two real setup requirements this surfaced**, both now handled by the script but
worth knowing:

- **The platform's service agent must be able to pull your image.** Registration
  fails with `FAILED_PRECONDITION ... could not access the container image` until
  the Reasoning Engine service agent
  (`service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com`) has
  `roles/artifactregistry.reader` on the repository. The script grants it.
- **Some env var names are reserved, which breaks the model region.** Setting
  `GOOGLE_CLOUD_PROJECT` or `GOOGLE_CLOUD_LOCATION` in the deployment env is
  rejected (`'GOOGLE_CLOUD_PROJECT' is reserved`); the platform injects those
  itself. That is a problem, not just a restriction: the platform sets
  `GOOGLE_CLOUD_LOCATION` to the **deploy region** (`us-central1`), but
  `gemini-3.7-flash` is served from `global`, so the first query fails with
  `NOT_FOUND ... models/gemini-3.7-flash was not found ... in the specified
  region`. The passthrough and the container are fine; the model lookup is in the
  wrong place. The fix is to pass the model's location in a var of *your own*
  (not a reserved one) and apply it before the agent imports.
  [main.py](../agent_runtime_byoc/main.py) reads `MODEL_LOCATION` and copies it over
  `GOOGLE_CLOUD_LOCATION` at startup:

  ```python
  if os.getenv("MODEL_LOCATION"):
      os.environ["GOOGLE_CLOUD_LOCATION"] = os.environ["MODEL_LOCATION"]
  # ...must run BEFORE `from demo_agent.agent import root_agent`,
  #    which initializes the genai client.
  ```

**You will see** your logs in **your** format, unlike 1.6. The tool line reads
`INFO - demo_agent.agent - tool get_weather called for city='Tokyo'` — the plain
`basicConfig` format from 1.5, not the platform's timestamped `agent.py:53` form
from 1.6:

```console
SEVERITY  TEXT_PAYLOAD
          INFO - google_adk.google.adk.models.google_llm - Sending out request, model: gemini-3.7-flash, backend: GoogleLLMVariant.VERTEX_AI, stream: False
          INFO - demo_agent.agent - tool get_weather called for city='Tokyo'
          INFO - google_adk.google.adk.models.google_llm - Response received from the model.
          INFO:     169.254.169.126:1392 - "POST /api/stream_reasoning_engine HTTP/1.1" 200 OK
```

> [!TIP]
> **What it means.** The BYOC container is the one place in Part 1 where, on Agent
> Runtime, you write the server and therefore own its logging config the way you do
> on Cloud Run: the format above is yours, because your `main.py` installed the
> handler, not the platform. That is the concrete contrast with 1.6, where the same
> agent's logs came out in the platform's format. The price is implementing the
> platform's two-endpoint contract and working around the reserved-var model-region
> trap. The two Agent Runtime deploys therefore differ mainly in logging: the
> managed agent object accepts the platform's format (1.6), and your own container
> keeps your own (1.7). Severity is still Default in both; that is Part 6's problem
> regardless of which you pick.

---

← Prev: [1. Log levels — local](01a-log-levels-local.md) · [Tutorial index](../TUTORIAL.md) · Next: [2. Access logs](02-access-logs.md) →

