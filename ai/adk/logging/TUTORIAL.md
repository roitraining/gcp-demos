# Logging for ADK agents on Cloud Run and Agent Runtime

This is a hands-on tutorial. You will run a small agent over and over, each time
changing one thing about how it logs, and read the actual output so you can see
what changed and why it matters. By the end you will know which logging
mechanism to use for local debugging, for a production service on Cloud Run, and
for a deployment on Vertex AI Agent Engine.

The reason logging an ADK agent is confusing is that there is no single "the
log." One agent process produces **four different streams**, configured in
different places:

1. **Your code** — ordinary `logging` records from your tools and business logic.
2. **The ADK framework** — everything ADK logs under the `google_adk` logger
   tree: model requests and responses, session lifecycle, tool calls.
3. **The web server** — when served over HTTP, uvicorn's own startup and access
   logs, on a config independent of ADK's.
4. **OpenTelemetry telemetry** — spans and GenAI events that do not print at all;
   they leave through an exporter you configure.

Almost every "why don't my logs look right" problem is really "I configured one
stream and expected it to cover another." Keep the four streams in mind as you
read.

> Verified against **google-adk 2.8.0** on Python 3.13, serving Gemini 3.7 Flash
> through Vertex AI. Every command and every output block below is from a real
> run. Version-sensitive details are called out inline.

## Setup

All commands run from this folder. Do this once.

### Create the environment

```bash
cd ai/adk/logging
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Point the agent at a model

Copy `.env.example` to `.env`. On GCP the simplest path is Vertex AI with your
existing `gcloud` credentials:

```bash
cp .env.example .env
# edit .env to contain:
#   GOOGLE_GENAI_USE_VERTEXAI=TRUE
#   GOOGLE_CLOUD_PROJECT=your-project-id
#   GOOGLE_CLOUD_LOCATION=global
gcloud auth application-default login   # if you have not already
```

### Meet the agent

Every example shares one tiny agent, [demo_agent/agent.py](demo_agent/agent.py):
a weather assistant with a single `get_weather` tool that knows four cities. The
tool logs a line of its own through a normal module logger. That means in every
example you can watch **your** log (stream 1) sit next to the **framework's** logs
(stream 2), and tell them apart by their logger name.

```python
logger = logging.getLogger(__name__)   # -> "demo_agent.agent", NOT under google_adk

def get_weather(city: str) -> dict:
    logger.info("tool get_weather called for city=%r", city)
    ...
```

One fact carries much of this tutorial: **all ADK framework loggers are children
of `google_adk`.** You configure them as a group with
`logging.getLogger("google_adk")`, and you can tell any framework line by its
name, for example `google_adk.google.adk.models.google_llm`.

## Part 1: the log level, and what each one shows you

**Why you are here.** The log level is the first and bluntest dial. Before adding
any plugin or custom formatter, you need to know exactly what `DEBUG`, `INFO`,
`WARNING`, and `ERROR` each reveal, so you can pick the right one instead of
drowning in output or flying blind. This part is a guided tour of that dial.

Part 1 runs the same one question, *"What's the weather in Tokyo?"*, three ways:
first through a plain script where you control the level directly (1.1), then
through each of the two servers ADK ships (1.2, 1.3).

### 1.1 The basic test harness

[examples/01_log_levels.py](examples/01_log_levels.py) runs that one question at
whichever level you name, using nothing but Python's standard `logging`: it sets
the root logger and the `google_adk` group to that level. No server, no HTTP, so
what you see is only streams 1 and 2.

#### 1.1.1 Start at INFO (the default)

```bash
.venv/bin/python examples/01_log_levels.py info
```

You will see:

```console
INFO - google_adk.google.adk.models.google_llm - Sending out request, model: gemini-3.7-flash, backend: GoogleLLMVariant.VERTEX_AI, stream: False
INFO - google_adk.google.adk.models.google_llm - Response received from the model.
INFO - demo_agent.agent - tool get_weather called for city='Tokyo'
INFO - google_adk.google.adk.models.google_llm - Sending out request, model: gemini-3.7-flash, backend: GoogleLLMVariant.VERTEX_AI, stream: False
INFO - google_adk.google.adk.models.google_llm - Response received from the model.

>>> ANSWER: The weather in Tokyo is currently 27°C and humid.
```

**What it means.** Those five lines are the agent loop, in order:

| Line | Logger | What happened |
|---|---|---|
| 1 | `google_adk...google_llm` | Framework sends your question to the model |
| 2 | `google_adk...google_llm` | Model answers: *call `get_weather`* |
| 3 | `demo_agent.agent` | **Your tool** runs (stream 1, not `google_adk`) |
| 4 | `google_adk...google_llm` | Framework sends the tool's result back |
| 5 | `google_adk...google_llm` | Model answers again, this time with prose |

Two things to take away. **One round trip per model call**: a tool call always
costs two, because the model must be re-asked once it has the tool's result.
**Your log sits in the middle of the framework's**, distinguishable only by
logger name, which is why the name prefix matters.

INFO gives you the **shape** of the run without the contents: which steps ran, in
what order, how many model calls. It does not show you the prompt or the answer.
That is the right trade for day-to-day "is it doing roughly the right thing."

#### 1.1.2 Turn it up to DEBUG

```bash
.venv/bin/python examples/01_log_levels.py debug
```

Now the same run dumps the full model conversation. The important new block is
`LLM Request`:

```console
LLM Request:
System Instruction:
You are a concise weather assistant. When the user asks about weather, call the
get_weather tool and report its result in one sentence...
Contents:
{"parts":[{"text":"What's the weather in Tokyo?"}],"role":"user"}
Functions:
get_weather: {'properties': {'city': {'title': 'City', 'type': 'string'}}, 'required': ['city'], ...}
LLM Response:
Function calls:
name: get_weather, args: {'city': 'Tokyo'}
```

**What it means.** DEBUG keeps every INFO line and adds the *contents* of each
model call. The new block breaks down as:

| Block | What it is | Where it came from |
|---|---|---|
| `System Instruction` | The agent's standing orders | your `instruction=` in `agent.py` |
| `Contents` | Full message history sent this call | the user turn, plus prior turns |
| `Functions` | Tool schema the model can choose from | generated from your Python signature and docstring |
| `LLM Response` | What came back, here a `functionCall` | the model |

The single most useful thing here is `Functions`. ADK builds that JSON schema
from your Python function's signature and docstring, and DEBUG is the only place
you can read what it actually generated. When a model refuses to call your tool,
or calls it with nonsense arguments, this block usually explains why.

So: INFO answers *what did the agent do*, DEBUG answers *what did the model
actually see*. Use DEBUG when the run is baffling and you need to stop guessing.
It is verbose and includes full response bodies, so it is a debugging level, not
something to leave on. (ADK omits auth headers from these dumps, so a DEBUG log
will not leak your bearer token.)

#### 1.1.3 Turn it down to WARNING, then ERROR

```bash
.venv/bin/python examples/01_log_levels.py warning
```

```console
>>> ANSWER: The weather in Tokyo is currently 27°C and humid.
```

**What it means.** Nothing from the framework at all, just your answer. At
WARNING and ERROR, a healthy run is silent; you only hear from the log when
something is wrong. Try asking about a city the tool does not know and you would
see the one `WARNING` line the tool itself emits (`no weather data for ...`).
This is why the guidance is **INFO or WARNING in production**: WARNING keeps the
log quiet until there is a problem, INFO gives you a lifecycle trail if you can
afford the volume. Reserve DEBUG for when you are actively debugging.

### 1.2 The same dial on `adk web`

In 1.1 you set the level in Python, with `logging`, the way any Python program
does. That is the real mechanism, and it is the only one that always applies.

The `adk` CLI adds a convenience on top of it: `adk web` and `adk api_server`
each take a **`--log_level`** flag (plus `-v`, shorthand for `--log_level
DEBUG`). The flag is not part of your agent and not part of the ADK library. It
belongs to those two commands, and all it does is make the same `logging` calls
on your behalf before starting the server. Launch the agent any other way and the
flag does not exist: in Part 5 you write your own server and configure logging
yourself, because there is no CLI in the picture to do it for you.

So: same dial as 1.1, reachable from the command line only because the ADK CLI is
the thing launching the process. Run it at `INFO` so the output lines up with
1.1.1.

Start the dev UI, open the URL it prints, pick **demo_agent** from the app
dropdown, and send the same question as before:

```bash
adk web --log_level INFO ./
```

```
What's the weather in Tokyo?
```

Watch the terminal, not the browser. You get the same five-line lifecycle trail
as the script: two `google_llm` round trips with your `tool get_weather called
for city='Tokyo'` line in the middle. Same agent, same level, same logs, only the
thing driving it has changed.

### 1.3 The same dial on `adk api_server`

`adk api_server` has no UI, so you drive it with HTTP. It is a two-step flow:
create a session, then post a message to it.

```bash
adk api_server --log_level INFO ./
```

In another terminal:

```bash
# 1. create a session (app name = the agent directory, demo_agent)
curl -s -X POST localhost:8000/apps/demo_agent/users/u1/sessions/s1 \
     -H 'content-type: application/json' -d '{}'

# 2. send the turn
curl -s -X POST localhost:8000/run \
     -H 'content-type: application/json' \
     -d '{"app_name":"demo_agent","user_id":"u1","session_id":"s1",
          "new_message":{"role":"user","parts":[{"text":"What'\''s the weather in Tokyo?"}]}}'
```

The response is the full JSON event list, one entry per step of the loop (the
model's `functionCall`, the tool's `functionResponse`, then the final text). To
pull out just the answer, pipe it through:

```bash
... | python3 -c "import sys,json; print([p['text'] for e in json.load(sys.stdin) for p in (e.get('content') or {}).get('parts',[]) if p.get('text')][-1])"
# The current weather in Tokyo is 27°C and humid.
```

If step 1 returns `409 Conflict`, that session id already exists: sessions are
persisted to `demo_agent/.adk/session.db` and survive restarts. Use a new id.

Now look at the server's terminal. The framework lines are the ones you expect,
but note the format, and note what is sitting between them:

```console
INFO:     127.0.0.1:57453 - "POST /apps/demo_agent/users/u1/sessions/s1 HTTP/1.1" 200 OK
2026-09-03 12:51:22,846 - INFO - google_llm.py:255 - Sending out request, model: gemini-3.7-flash, backend: GoogleLLMVariant.VERTEX_AI, stream: False
2026-09-03 12:51:24,418 - INFO - google_llm.py:327 - Response received from the model.
2026-09-03 12:51:24,435 - INFO - agent.py:40 - tool get_weather called for city='Tokyo'
2026-09-03 12:51:24,443 - INFO - google_llm.py:255 - Sending out request, model: gemini-3.7-flash, backend: GoogleLLMVariant.VERTEX_AI, stream: False
2026-09-03 12:51:25,170 - INFO - google_llm.py:327 - Response received from the model.
2026-09-03 12:51:25,174 - INFO - api_server.py:1854 - Generated 3 events in agent run
INFO:     127.0.0.1:57455 - "POST /run HTTP/1.1" 200 OK
```

Two different formats in one stream. The timestamped lines are the framework and
your tool, formatted by the ADK CLI. The bare `INFO:` lines are uvicorn's access
log, one per HTTP request.

Now turn the dial down and watch what does *not* happen. Restart with
`--log_level WARNING` and send the same two requests:

```console
INFO:     Started server process [12706]
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:58393 - "POST /apps/demo_agent/users/u1/sessions/w1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:58395 - "POST /run HTTP/1.1" 200 OK
```

Every timestamped line is gone, exactly as 1.1.3 taught you to expect. But the
`INFO:` lines are still there, at INFO, after you asked for WARNING. The flag did
not fail: those lines are stream 3, and `--log_level` never reaches it. That is
what Part 2 is about.

One trap worth knowing now: `adk run` (the terminal REPL) does **not** print
framework logs to your screen. It redirects them to a temp file and clears the
console handlers. If you use it and wonder where the logs went:

```bash
tail -F "${TMPDIR:-/tmp}/agents_log/agent.latest.log"
```

### 1.4 The same script on Cloud Run, and what Cloud Logging does to it

**Why you are here.** So far every run was on your laptop, where a log line is
just text on your terminal. The moment you deploy, a second system gets an
opinion about your logs: Cloud Logging reads each line, assigns it a
**severity**, and files it under a stream. Before you write a single line of
cloud-specific logging (Part 6 does that), you should see what Cloud Logging
makes of the *unmodified* Part 1 script, because the answer is not what the
common advice says.

The script from 1.1 runs once and exits; it serves no HTTP. The right way to
run it on Cloud Run is a **Job**, not a service (a service would fail
its readiness check with no port to probe). A Job runs the container to
completion, and Cloud Run ingests its stdout and stderr into Cloud Logging
automatically. [deploy/deploy_job.sh](deploy/deploy_job.sh) builds the image,
deploys the Job, and runs it once; the level is a Job argument, so you can
re-run at a different level without rebuilding.

**Do this.** Deploy and run at INFO, then run again at WARNING:

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

**What it means, finding one: the level dial works in the cloud, unchanged.**
The WARNING execution shows the banner and the answer and *no* `google_adk` or
tool lines; the INFO execution shows the whole five-line lifecycle you know from
1.1.1. Nothing about deploying changed what the level controls. This is the
reassuring half.

**What it means, finding two: severity is not what you were told.** There is a
rule repeated all over the Cloud Run docs and even in ADK's own source comments:
*a line written to stderr is recorded as ERROR severity regardless of content.*
`logging.basicConfig` writes to stderr, so by that rule every `INFO -
google_adk...` line above should read as ERROR. Look at the severity column: it
does not. Those lines came through with **blank (Default) severity, not ERROR**.
You can confirm they really are on stderr:

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

> One display note: Cloud Run batches burst console output, so several of the
> script's lines can arrive grouped under one Cloud Logging entry (you will see
> the `===== running =====` banner and the lifecycle lines share an entry
> above). That is a grouping artifact of the read, not a change to your logs.

### 1.5 The same logging behind a real HTTP server

**Why you are here.** A Job runs once and exits. A real service stays up and
takes requests, which adds the one stream a script never has: the web server's
own access log (stream 3 from the introduction). This section deploys the
smallest possible ADK HTTP server, one that does *nothing* special about
logging, so you can see all of Part 1's streams land in Cloud Logging together,
and confirm on a long-running service what 1.4 found on a Job.

[examples/09_min_api.py](examples/09_min_api.py) is that server. It is
deliberately naive: it configures logging with the exact `configure(level)` from
1.1 (a level plus `logging.basicConfig`), reads the level from a `LOG_LEVEL`
environment variable, and starts uvicorn **without** a log config, so uvicorn's
own default access logging is left untouched. It exposes one real route,
`POST /chat`, and a `GET /healthz`. That is the whole server. (Contrast it with
the servers in Parts 5 and 6, which take control of every stream; this one takes
control of none, on purpose.)

**Do this.** Deploy it (unauthenticated, for demo simplicity), then send the same
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

**What it means.** Four sources, interleaved, exactly as they were on your
laptop: your server's own `agent.server` line, the `google_adk` framework lines,
your tool's `demo_agent.agent` line, and, new for a server, uvicorn's
`INFO: ... "POST /chat HTTP/1.1" 200 OK` access line. Nothing here is
cloud-shaped; it is the raw Part 1 output, now arriving from a container.

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

**What it means.** `LOG_LEVEL=warning` reached streams 1 and 2 (your code and
`google_adk`), which is why the lifecycle lines vanished, exactly as 1.1.3 taught
you. It did **not** reach uvicorn's access log: the `"POST /chat" 200 OK` line
prints regardless, because that stream is configured by uvicorn, not by your
level. That is the whole of Part 2, now visible in the cloud: on a busy service
this is one access line per request forever, health checks included, no matter
how far down you turn your level. Part 2 fixes it; Part 6 makes the rest of these
lines into structured entries with severity you can query.

> If, right after a WARNING redeploy, you still see a few `google_adk` lines,
> they are from the previous INFO revision still inside the read's freshness
> window (you will see `Reason: DEPLOYMENT_ROLLOUT` entries marking the switch).
> Wait for the old revision to drain, or narrow `--freshness`.

### 1.6 The same agent on Agent Runtime, where the platform logs for you

**Why you are here.** Cloud Run (1.4, 1.5) gave you a container and got out of
the way: whatever you wrote to stdout/stderr is what you got. Agent Runtime
(Vertex AI Agent Engine) is the other place you deploy, and it is different in a
way that matters for logging: you deploy the **agent**, not a web server, and the
platform runs it for you. That means the platform, not your code, decides how
your logs are handled. This section shows exactly which parts of Part 1 you still
control there, and which the platform takes over.

You deploy with `adk deploy agent_engine`, which packages the agent directory and
hands it to the platform. There is no server of yours in the picture, so there is
no `uvicorn.run` and no `configure()` call at a `__main__`. The one hook you have
for the log level is an environment variable: `demo_agent/agent.py` reads
`LOG_LEVEL` at import and applies it (this tutorial added that). `adk deploy
agent_engine` has no env flag, but it carries the agent directory's `.env` into
the deployment, so [deploy/deploy_agent_engine.sh](deploy/deploy_agent_engine.sh)
writes `LOG_LEVEL` there before deploying.

**Do this.** Deploy at INFO, note the reasoning engine id it prints, and send one
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

**What it means: the platform owns your log format and stream, you keep the
level.** Compare that tool line to 1.5. On Cloud Run it read
`INFO - demo_agent.agent - tool get_weather...`, your `basicConfig` format. Here
it reads `2026-09-03 21:51:45,037 - INFO - agent.py:53 - tool get_weather...`,
the ADK CLI's timestamped `file:line` format, the same one you saw from
`adk api_server` back in 1.3. Your `basicConfig(format=...)` did not take: the
platform installs its own logging handler before your module runs, so it decides
the format and the destination (stderr), and your handler config is ignored.

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

> Two traps. First, `adk deploy agent_engine` **creates a new reasoning engine on
> every deploy**; it does not update in place, so the WARNING redeploy has a new
> `ENGINE_ID`. Delete the old ones when you are done (the deploy script prints the
> teardown command). Second, `adk deploy` exits 0 even when the underlying deploy
> failed, so the query is the real success check, not the exit code.

### 1.7 The same server as a custom container on Agent Runtime

**Why you are here.** 1.6 deployed the agent object and let the platform serve it.
But Agent Runtime also accepts a **container you build yourself** (bring your own
container), which is how you run 1.5's kind of hand-written server on the managed
platform instead of on Cloud Run. The catch is that the platform's contract
constrains what that container must be.

A custom container on Agent Runtime is not free-form. The runtime contract
requires it to listen on **port 8080** and implement two specific routes,
`POST /api/reasoning_engine` (unary) and `POST /api/stream_reasoning_engine`
(streaming), each taking a `{"class_method", "input"}` body. A plain `/chat`
route like 1.5's is therefore not enough on its own. The smallest server that
satisfies the contract wraps the agent in `vertexai.agent_engines.AdkApp` and
dispatches the named method to it; that is what
[agent_runtime_byoc/main.py](agent_runtime_byoc/main.py) does, in about ninety
lines. Its logging is deliberately the same naive Part 1 config as 1.5. This
section tests whether your own container gives you your logging format back, or
the platform overrides it the way it did in 1.6.

**Do this.** Build, push, and register the container, then query it through the
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
  [main.py](agent_runtime_byoc/main.py) reads `MODEL_LOCATION` and copies it over
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

**What it means.** The BYOC container is the one place in Part 1 where, on Agent
Runtime, you write the server and therefore own its logging config the way you do
on Cloud Run: the format above is yours, because your `main.py` installed the
handler, not the platform. That is the concrete contrast with 1.6, where the same
agent's logs came out in the platform's format. The price is implementing the
platform's two-endpoint contract and working around the reserved-var model-region
trap. The two Agent Runtime deploys therefore differ mainly in logging: the
managed agent object accepts the platform's format (1.6), and your own container
keeps your own (1.7). Severity is still Default in both; that is Part 6's problem
regardless of which you pick.

## Part 2: why the level flag does not silence access logs

**Why you are here.** You saw it at the end of 1.3: `--log_level WARNING`
silenced the whole framework and your tool, and the `INFO:` access lines kept
right on printing. That is a small annoyance on your laptop and a real problem in
production, where it means one log line per request forever, including a flood
from your load balancer's health checks, no matter how far down you turn the
flag.

**The flag worked. It just does not reach this stream.** Recall the four
streams. `--log_level` configures streams 1 and 2 (your code and `google_adk`).
The request/access lines come from stream 3, uvicorn's `uvicorn.access` logger,
and **uvicorn configures that logger itself**, with its own level and its own
handler, the moment it starts. ADK launches uvicorn without overriding that, so
the access logger stays at its own INFO regardless of what you passed to
`--log_level`. This is not an ADK quirk; it is how every uvicorn/FastAPI app
behaves. The access log is simply a different stream than the one the flag
controls.

Once you see it that way, the fix is obvious: when you run your own server, hand
uvicorn a logging config and put a filter on `uvicorn.access`. The key piece from
[examples/02_tame_uvicorn.py](examples/02_tame_uvicorn.py) drops health-check
paths entirely:

```python
class DropHealthChecks(logging.Filter):
    NOISY_PATHS = ("/healthz", "/health", "/readyz", "/livez")

    def filter(self, record):
        # uvicorn.access record.args = (client, method, path, http_version, status)
        if record.args and len(record.args) >= 3:
            path = str(record.args[2])
            if any(path.startswith(p) for p in self.NOISY_PATHS):
                return False   # drop this record
        return True
```

**Do this.** Start the demo server, then hit the health endpoint three times and
the root once:

```bash
.venv/bin/python examples/02_tame_uvicorn.py
# in another terminal:
curl -s localhost:8081/healthz    # run this 3 times
curl -s localhost:8081/           # then this once
```

**You will see**, in the server terminal:

```console
2026-08-31 20:08:06 - ACCESS - 127.0.0.1:51868 "GET / HTTP/1.1" 200 OK
```

**What it means.** Three health checks produced **zero** log lines; the one real
request produced exactly one. You did not lower a level, you filtered a specific
stream. On a busy service, that removes one log line per health check for the
life of the deployment. It also sets up the rest of this tutorial: to control
agent logging well, you stop relying on a global level and start configuring each
stream deliberately.

## Part 3: a readable narration of the agent's steps

**Why you are here.** INFO is too terse to debug a tool-calling problem (it tells
you a request happened, not what the tool was called with), and DEBUG dumps the
full model conversation as raw JSON. In development you often want the middle
ground: a clean, human-readable narration of the agentic steps, which tool ran,
with which arguments, what it returned, how many tokens it cost, without writing
that yourself. ADK ships two plugins for exactly this. This part uses them
locally first, then deploys each one to Cloud Run so you can see what a plugin
sends to Cloud Logging, and closes with when to reach for a plugin at all.

### 3.1 LoggingPlugin: one line to wire up

A plugin attaches to the `App`. That is the whole setup, shown in
[examples/03_logging_plugin.py](examples/03_logging_plugin.py):

```python
from google.adk.apps.app import App
from google.adk.plugins import LoggingPlugin

app = App(name="demo", root_agent=root_agent, plugins=[LoggingPlugin()])
```

The plugin's own docstring is blunt about its scope: it "is not a replacement of
existing logging in ADK," but rather "helps terminal based debugging" and
"serves as a simple demo for everyone to leverage when developing new plugins."
Read this section as much for how to write a plugin as for what this one prints.
The two deployed sections that follow (3.2, 3.4) are optional. We ran these
plugins on Cloud Run to satisfy a fair question, what would the cloud even do
with them, and the answer is instructive. But the takeaway is that you would not
actually ship either one; skip ahead to Part 4 if you only want the production
path.

**How the one line works.** A plugin is a set of lifecycle hooks. `BasePlugin`
declares fourteen async callbacks, `on_user_message_callback`,
`before_run_callback`, `before/after_agent_callback`,
`before/after_model_callback`, `before/after_tool_callback`, `on_event_callback`,
`after_run_callback`, three error hooks, and `close`, and every one returns
`None` by default. A plugin subclass overrides only the hooks it cares about.
`App(plugins=[...])` hands the list to a `PluginManager`, and at each point in a
run the runner calls the matching hook on every plugin, in registration order,
before any per-agent callback. The manager uses an early-exit rule:

> if any plugin
> callback returns a non-`None` value, the execution of subsequent plugins for
> that specific event is halted, and the returned value is propagated up the
> call stack.

`LoggingPlugin` returns `None` from every hook, so it never short-circuits
anything. It is a pure observer that prints and gets out of the way.

**What "no arguments" configures.** `LoggingPlugin()` takes only an optional
`name`; nothing else is configurable:

```python
def __init__(self, name: str = "logging_plugin"):
    super().__init__(name)
```

Everything about how it writes is fixed in the source:

| Setting | Value | Where |
|---|---|---|
| Line prefix | `[logging_plugin]`, the `name` | `_log` |
| Sink | `print()` to stdout, wrapped in grey ANSI codes | `_log` |
| Level, handler, formatter | none; the `logging` module is never touched | whole file |
| Text and system-instruction length | truncated at 200 characters | `_format_content` |
| Tool arguments and results length | truncated at 300 characters | `_format_args` |

The sink is the whole story, and it is four lines:

```python
def _log(self, message: str) -> None:
    # ANSI color codes: \033[90m for grey, \033[0m to reset
    formatted_message: str = f"\033[90m[{self.name}] {message}\033[0m"
    print(formatted_message)
```

Each hook just formats a few fields and calls `_log`. For example the
`TOOL STARTING` block you will see below is produced by `before_tool_callback`:

```python
async def before_tool_callback(self, *, tool, tool_args, tool_context):
    self._log(f"🔧 TOOL STARTING")
    self._log(f"   Tool Name: {tool.name}")
    self._log(f"   Agent: {tool_context.agent_name}")
    self._log(f"   Function Call ID: {tool_context.function_call_id}")
    self._log(f"   Arguments: {self._format_args(tool_args)}")
    return None
```

Because everything goes through `print()`, neither `--log_level` nor a
`dictConfig` can reach this output. That is the trait that decides where you use
it, called out at the end of this section.

**Do this.**

```bash
.venv/bin/python examples/03_logging_plugin.py
```

The example asks *"What's the weather in London?"* **You will see** the whole
invocation narrated, one hook at a time (lightly trimmed, repeated field lines
removed):

```console
[logging_plugin] 🚀 USER MESSAGE RECEIVED
[logging_plugin]    User Content: text: 'What's the weather in London?'
[logging_plugin] 🏃 INVOCATION STARTING
[logging_plugin] 🤖 AGENT STARTING
[logging_plugin]    Agent Name: weather_agent
[logging_plugin] 🧠 LLM REQUEST
[logging_plugin]    Model: gemini-3.7-flash
[logging_plugin]    System Instruction: 'You are a concise weather assistant. ...'
[logging_plugin]    Available Tools: ['get_weather']
[logging_plugin] 🧠 LLM RESPONSE
[logging_plugin]    Content: function_call: get_weather
[logging_plugin]    Token Usage - Input: 167, Output: 16
[logging_plugin] 📢 EVENT YIELDED
[logging_plugin]    Function Calls: ['get_weather']
[logging_plugin] 🔧 TOOL STARTING
[logging_plugin]    Tool Name: get_weather
[logging_plugin]    Arguments: {'city': 'London'}
[logging_plugin] 🔧 TOOL COMPLETED
[logging_plugin]    Result: {'status': 'ok', 'report': 'The weather in London is 15C and drizzling.'}
[logging_plugin] 📢 EVENT YIELDED
[logging_plugin]    Function Responses: ['get_weather']
[logging_plugin] 🧠 LLM REQUEST
[logging_plugin] 🧠 LLM RESPONSE
[logging_plugin]    Content: text: 'The weather in London is currently 15°C and drizzling.'
[logging_plugin]    Token Usage - Input: 228, Output: 15
[logging_plugin] 📢 EVENT YIELDED
[logging_plugin]    Final Response: True
[logging_plugin] 🤖 AGENT COMPLETED
[logging_plugin] ✅ INVOCATION COMPLETED
```

**What it means.** That is the full agentic loop, in order: the model saw the
tools and chose `get_weather`, the tool ran with `{'city': 'London'}` and
returned its report, the model was called a second time with that result and
produced the final text, and the run ended. Two model calls, one tool call, and
their token costs (167 plus 16 to decide the call, 228 plus 15 to write the
answer), all without parsing DEBUG. This is the view you want when a tool is
called with the wrong arguments, or not called when it should be.

**What you will not see.** `LLM REQUEST` prints the model, the first 200
characters of the system instruction, and the tool names, but not the
conversation contents. The source removed that on purpose:

```python
# Note: Content logging removed due to type compatibility issues
# Users can still see content in the LLM response
```

So the exact prompt sent to the model is still a DEBUG or `DebugLoggingPlugin`
job, which is what 3.3 is for.

> **The catch that decides where you use it.** `LoggingPlugin` writes with
> `print()` and ANSI color codes, **not** through the `logging` module. That is
> perfect in a terminal and wrong for a deployed service: it ignores your
> handlers, levels, and formatters, and the color bytes corrupt a JSON log line.
> Use it for local debugging. When you need this information *in production*, use
> the structured plugin in Part 4 instead. The next section shows exactly what
> that catch looks like once the same script runs on Cloud Run.

### 3.2 LoggingPlugin on Cloud Run

**Optional. Why you are here.** You would not deploy `LoggingPlugin` to a real
service; this section exists only to satisfy the natural curiosity about what
Cloud Run does with a print-based plugin, and the answer turns the 3.1 callout
from a claim into evidence. It is the same move as 1.4: deploy the unmodified
script as a Cloud Run Job, run it, and read back what Cloud Logging did with each
line.
[deploy/deploy_plugin_job.sh](deploy/deploy_plugin_job.sh) builds one image that
can run either plugin example; the script to run is the Job argument, and
`LOG_LEVEL` is an environment variable, so you can change the framework level
between runs without rebuilding. Example 03 configures no logging of its own, so
`LOG_LEVEL` controls only the framework logger (stream 2), never the plugin.

**Do this.** Deploy and run once at INFO, then run again at WARNING:

```bash
export PROJECT_ID=your-project REGION=us-central1
SCRIPT=examples/03_logging_plugin.py ./deploy/deploy_plugin_job.sh   # deploys adk-plugin-job, runs at INFO
gcloud run jobs execute adk-plugin-job \
  --project="$PROJECT_ID" --region="$REGION" \
  --update-env-vars=LOG_LEVEL=WARNING --wait
```

Then read the plugin's own lines, and separately the framework's, back:

```bash
# The plugin narration (stdout):
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-plugin-job"
   textPayload:"logging_plugin"' \
  --project="$PROJECT_ID" --limit=10 \
  --format='value(severity,textPayload)' --freshness=15m

# The framework lines (stderr):
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-plugin-job"
   textPayload:"google_adk"' \
  --project="$PROJECT_ID" --limit=10 \
  --format='value(severity,textPayload)' --freshness=15m
```

**You will see** two things worth stopping on.

First, the narration is unchanged by the level. Both the INFO run and the
WARNING run carry the full `[logging_plugin]` narration; the WARNING run just has
no `google_adk` lines next to it. The framework query returns rows for the INFO
run and nothing for the WARNING run:

```console
INFO - google_adk.google.adk.plugins.plugin_manager - Plugin 'logging_plugin' registered.
INFO - google_adk.google.adk.models.google_llm - Sending out request, model: gemini-3.7-flash, ...
INFO - google_adk.google.adk.models.google_llm - Response received from the model.
```

Second, the narration reaches the cloud as raw terminal bytes. The severity
column is blank (Default) for every plugin line, and the ANSI codes arrive
literally in the payload:

```console
<no severity>  ^[[90m[logging_plugin] 🔧 TOOL STARTING^[[0m
<no severity>  ^[[90m[logging_plugin]    Arguments: {'city': 'London'}^[[0m
```

**What it means, finding one: the plugin is independent of the level dial.**
Turning stream 2 down to WARNING removed the framework's lifecycle lines and left
the plugin narration completely intact, because the plugin never goes through
`logging`. That is exactly what makes it great in development, and exactly why it
is the wrong tool in production: you cannot turn it down without deleting it from
the code.

**What it means, finding two: the narration is not queryable.** Every plugin
line lands on stdout with Default severity and its grey ANSI codes embedded in
the text. It is readable in the console, but nothing in it is a field you can
filter, alert on, or group. (The `google_adk` lines have the same problem 1.4
found: they are on stderr and still come through as Default, not ERROR.) Making
this information queryable is the job of Part 4, which feeds the same hook data
through the `logging` module instead of `print()`.

Tear down when you are done:

```bash
gcloud run jobs delete adk-plugin-job --project="$PROJECT_ID" --region="$REGION" --quiet
```

### 3.3 DebugLoggingPlugin: capture one whole turn to a file

**Why.** Sometimes one specific turn misbehaves and you want the complete,
inspectable record to diff or attach to a bug report, not a stream you have to
watch live.

```python
from google.adk.plugins import DebugLoggingPlugin
plugin = DebugLoggingPlugin(output_path="adk_debug.yaml")
```

**How it differs from `LoggingPlugin`.** Both subclass `BasePlugin` and override
the same hooks, but almost everything else is opposite:

| | `LoggingPlugin` | `DebugLoggingPlugin` |
|---|---|---|
| Sink | `print()` to stdout | a YAML file |
| When it writes | immediately, at every hook | buffered in memory, written once per invocation in `after_run_callback` |
| Detail | truncated; no request contents | full request contents, config, tool list, responses, session state |
| Redaction | none | credential models, secret-named keys, private-key blocks, all `temp:` state |
| File safety | not applicable | created `0600`; warns once if an existing file is wider |
| Own diagnostics | none | emits real `logging` warnings and errors |

Its constructor exposes the knobs the terminal plugin does not have, all
keyword-only:

```python
def __init__(
    self,
    *,
    name: str = "debug_logging_plugin",
    output_path: str = "adk_debug.yaml",
    include_session_state: bool = True,
    include_system_instruction: bool = True,
):
```

Where `LoggingPlugin` formats a line and prints it, this plugin records the
request as structured data. Its `before_model_callback` keeps the whole thing:

```python
request_data = {
    "model": llm_request.model,
    "content_count": len(llm_request.contents),
    "contents": [self._serialize_content(c) for c in llm_request.contents],
}
if llm_request.tools_dict:
    request_data["tools"] = list(llm_request.tools_dict.keys())
self._add_entry(callback_context.invocation_id, "llm_request", **request_data)
```

Nothing is written until the invocation ends. `after_run_callback` dumps the
buffered entries as one YAML document, and it takes care to create the file
readable only by its owner:

```python
fd = os.open(self._output_path,
             os.O_WRONLY | os.O_CREAT | os.O_APPEND, _OUTPUT_FILE_MODE)  # 0o600
with os.fdopen(fd, "a", encoding="utf-8") as f:
    f.write("---\n")
    yaml.dump(output_data, f, default_flow_style=False,
              allow_unicode=True, sort_keys=False, width=120)
```

**Do this**, then open the file it writes:

```bash
.venv/bin/python examples/04_debug_plugin.py
cat adk_debug.yaml
```

Example 04 passes `include_session_state=True` and
`include_system_instruction=True` explicitly. Both are already the defaults; they
are written out so you can see the knobs exist.

**You will see** one YAML document for the invocation, a list of timestamped
entries:

```console
- timestamp: '2026-09-03T23:54:59.413524'
  entry_type: llm_request
  data:
    model: gemini-3.7-flash
    contents:
    - role: user
      parts:
      - text: What's the weather in a city you don't know, like Paris?
    tools:
    - get_weather
```

The `entry_type` values, in order, trace the same lifecycle the terminal plugin
narrates: `invocation_start`, `agent_start`, `llm_request`, `llm_response`,
`event`, `tool_call`, `tool_response`, `event`, a second `llm_request` and
`llm_response`, `event`, `agent_end`, `session_state_snapshot`,
`invocation_end`.

**What it means.** It is the full turn on disk: exact prompt, system instruction,
tool arguments, tool results, token counts, and session state. Two properties
matter. It is buffered, so nothing reaches the file until the invocation
completes; if the process dies mid-turn, that turn is lost. And it redacts by
design, but broadly:

> That last rule blanks all temporary state, not
> only credentials, so an intermediate value passed between agents under a
> `temp:` key reads as `[REDACTED]` here.

The file still holds full prompt content, so it is created `0600` and should be
treated as sensitive. This is a debugging capture, not a log sink you leave
running. Example 04 also reads its output path from a `DEBUG_OUTPUT` environment
variable when one is set, which the next section uses to redirect the capture off
the container.

### 3.4 DebugLoggingPlugin on Cloud Run

**Optional. Why you are here.** Like 3.2, this is a curiosity-driven detour, not
a step you need. You would not run `DebugLoggingPlugin` on Cloud Run in practice,
but doing it once teaches a real lesson about file-writing tools in ephemeral
containers. 3.3 wrote a file; a Cloud Run Job's filesystem is thrown away when
the execution ends. So where does the capture go?

**Do this**, part one, the naive deploy:

```bash
SCRIPT=examples/04_debug_plugin.py ./deploy/deploy_plugin_job.sh   # deploys adk-debug-plugin-job
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-debug-plugin-job"' \
  --project="$PROJECT_ID" --limit=20 \
  --format='value(severity,textPayload)' --freshness=15m
```

**You will see** the script's two `print()` lines and nothing resembling the
YAML:

```console
FINAL ANSWER: I do not have weather data for Paris.
Full invocation captured to: /app/adk_debug.yaml
WARNING - google_adk.google.adk.plugins.debug_logging_plugin - No debug state for invocation e-..., skipping entry
```

The file was written to `/app/adk_debug.yaml` inside the container and discarded
with it. (The `skipping entry` warning is a harmless ADK ordering quirk: the
plugin's `on_user_message_callback` fires before `before_run_callback` creates
the per-invocation buffer, so the first entry is dropped. Notice it is a real
`logging` record on stderr, unlike anything `LoggingPlugin` emits.)

**What it means.** A file-writing plugin needs a filesystem that outlives the
execution. Cloud Run can mount a Cloud Storage bucket as a volume, and example 04
already reads its path from `DEBUG_OUTPUT`.

**Do this**, part two, mount a bucket:

```bash
export BUCKET="${PROJECT_ID}-adk-debug"   # any bucket you own; created in $REGION if missing
MOUNT=1 SCRIPT=examples/04_debug_plugin.py ./deploy/deploy_plugin_job.sh
gcloud storage cat "gs://$BUCKET/adk_debug.yaml" | head -40
```

With `MOUNT=1` the deploy script mounts `$BUCKET` at `/mnt/out` and sets
`DEBUG_OUTPUT=/mnt/out/adk_debug.yaml` on the Job.

**You will see** the same YAML document as 3.3, now read back from the bucket,
with the full `entry_type` sequence intact. Check Cloud Logging for one more
line the plugin emits about the file it just wrote:

```console
WARNING - google_adk.google.adk.plugins.debug_logging_plugin - Debug output file /mnt/out/adk_debug.yaml is readable beyond its owner and holds whole prompts and responses; restrict it to mode 600.
```

**What it means.** The plugin behaved exactly as on your laptop; only the disk
changed. The mode warning is the plugin doing its job: the Cloud Storage FUSE
mount reports a mode wider than `0600`, so the plugin cannot guarantee the file
is owner-only and says so, through the `logging` module, on stderr. Two cautions
follow from that. The capture now lives in a bucket and still holds full prompts,
so bucket IAM is your new `0600`. And this is still a debugging capture, not a
log pipeline; if you find yourself running it routinely in the cloud, you want
the structured plugin in Part 4 instead.

> A quick alternative, if you only need the capture once and do not want a
> bucket: have the script `cat` the file to stdout at the end, and it lands in
> Cloud Logging as one large text payload. It works, but it throws away the
> "file, not stream" property that made the plugin worth using.

Tear down when you are done:

```bash
gcloud run jobs delete adk-debug-plugin-job --project="$PROJECT_ID" --region="$REGION" --quiet
```

### 3.5 Plugin or level dial?

**Why you are here.** You have now seen both plugins, locally and deployed. When
should you reach for one instead of just turning the `google_adk` level up? The
short answer: when you want structured facts about the agent's steps rather than
the framework's own log prose.

Built-in ADK logging is text lines under `google_adk`, at whatever level you set.
A plugin hooks the same lifecycle but receives objects, at named points, before
those lines are ever formatted. That difference buys four things:

| Benefit | What it means in practice |
|---|---|
| Objects, not strings | `after_model_callback` receives an `LlmResponse` with `usage_metadata`; you read token counts as numbers, never parse a DEBUG dump |
| Independent of the level | 3.2 proved it: WARNING silenced the framework and the plugin narration kept going |
| One registration, app-wide | a plugin fires for every agent and tool in the `App`; a per-agent callback has to be wired onto each agent |
| You own the sink | the same hook data feeds `print()` (3.1), a YAML file (3.3), JSON `logging` records (Part 4), or BigQuery |

What the level dial still does better: DEBUG shows the framework's own internals,
the wire-level request, HTTP retries, and session-service work, none of which
have plugin hooks. The two are complementary, not rivals.

Three cases where a plugin is the right call:

1. **A tool is getting the wrong arguments in development.** Run the framework at
   WARNING so its lines are quiet, attach `LoggingPlugin`, and watch the
   `Arguments:` lines. You see the tool calls and nothing else.
2. **You need a reproducible bug report.** Attach `DebugLoggingPlugin`, reproduce
   the turn, and attach the YAML. Or capture one document before a prompt change
   and one after, and diff them. From a Cloud Run Job, that means the mounted
   bucket from 3.4.
3. **You are watching token cost while tuning a prompt.** Read `Token Usage` per
   model call from `LoggingPlugin`, or `usage_metadata` from the YAML, with no
   formatter to write. When you want those numbers queryable in production, Part
   4 turns the same hook into structured log fields.

## Part 4: production logging you own

**Why you are here.** You want the visibility of Part 3, but for a running
service you can query, alert on, and correlate. That rules out `LoggingPlugin`
(it prints) and DEBUG (it is unstructured text). The answer is to write a small
plugin whose callbacks emit **real `logging` records** with structured fields.
Because they go through the `logging` module, your handlers and formatters apply,
so the *same plugin* prints readable text on your laptop and clean JSON in the
cloud (Part 6). Write it once, reuse it everywhere you deploy.

A plugin's callbacks are the hook points. From
[examples/05_structured_plugin.py](examples/05_structured_plugin.py), the
"after model" hook records latency and token usage:

```python
class StructuredTelemetryPlugin(BasePlugin):
    async def after_model_callback(self, *, callback_context, llm_response):
        usage = getattr(llm_response, "usage_metadata", None)
        telemetry_log.info("llm_response", extra={
            "event": "llm_response",
            "agent": callback_context.agent_name,
            "latency_ms": ...,                       # measured in the plugin
            "input_tokens": getattr(usage, "prompt_token_count", None),
            "output_tokens": getattr(usage, "candidates_token_count", None),
        })
        return None   # returning None means "proceed normally"
```

**Do this.** The example attaches a JSON formatter to the telemetry logger and
asks *"What's the weather in New York?"*:

```bash
.venv/bin/python examples/05_structured_plugin.py
```

**You will see** one structured line per event:

```console
{"severity": "INFO", "message": "llm_response", "agent": "weather_agent", "latency_ms": 1617.0, "input_tokens": 141, "output_tokens": 6}
{"severity": "INFO", "message": "tool_start", "tool": "get_weather", "tool_args": {"city": "New York"}}
{"severity": "INFO", "message": "tool_end", "tool": "get_weather", "latency_ms": 0.2, "status": "ok"}
```

**What it means.** Every line is now a machine-readable event, not prose. That is
the prerequisite for querying: the fields you see here (`latency_ms`, `status`,
`input_tokens`) become keys you can filter, aggregate, and alert on the moment
these lines reach a log store. Nothing here is terminal-specific either, so the
same script proves the point in the cloud.

**Do this on Cloud Run.** Example 05 runs once and exits, so it is a Cloud Run
Job, exactly like the plugin scripts in 3.2 and 3.4, and the same deploy helper
takes this script as its argument:

```bash
export PROJECT_ID=your-project REGION=us-central1
SCRIPT=examples/05_structured_plugin.py ./deploy/deploy_plugin_job.sh
```

Cloud Run ingests the container's stdout automatically, and because each line is
JSON, Cloud Logging parses it into a `jsonPayload` object with your fields as keys.
The claim above is now a real query, filtering to one event type and reading
latency as a number:

```bash
gcloud logging read \
  'resource.type="cloud_run_job" jsonPayload.event="tool_end"' \
  --project="$PROJECT_ID" --freshness=15m \
  --format='table(jsonPayload.tool, jsonPayload.latency_ms, jsonPayload.status)'
```

**You will see** the structured fields returned as query columns, not text you
have to parse:

```console
TOOL         LATENCY_MS  STATUS
get_weather  0.5         ok
```

**What it means.** No formatter change was needed: the JSON you saw on your laptop
is the JSON Cloud Logging indexed. `jsonPayload.status="error"` is now an alerting
condition and `jsonPayload.latency_ms` is a metric you can chart, both because the
plugin emitted structured fields instead of prose, and `severity` rode along in
the JSON, so Cloud Logging shows these as `INFO` rather than guessing. Part 6
extends that to a long-running Service, putting the same correct severity *and* a
shared trace id on **every** stream, including the framework and access logs your
plugin never touches, so all of one request's lines group together. Tear down the
job when you are done:

```bash
gcloud run jobs delete adk-structured-job --project="$PROJECT_ID" --region="$REGION" --quiet
```

One detail this example teaches by doing:

- **Reserved field names.** Keys in `extra=` must not collide with built-in
  `LogRecord` attributes (`args`, `name`, `message`, `module`). The example uses
  `tool_args`, not `args`, precisely because `args` collides and raises a
  `KeyError` inside the log call. (This one bites everyone once.)

### 4.1 Callback or plugin?

**Why you are here.** The plugin above is one of two ways to emit your own
records; the other is a per-agent callback, and you have probably seen that style
elsewhere. Before choosing between them, be clear on what this logging is for. It
does not replace ADK's built-in logging. It sits alongside it, because the two
answer different questions.

To operate the agent you have to be able to answer questions like:

1. Is the model call failing or being retried?
2. Which tool ran, with which arguments, and did it succeed?
3. How many tokens did this turn cost, and what is a session costing?

Set a level on `google_adk` and the framework answers the first on its own:
requests sent, responses received, retries, and errors, for free. It does not
answer the second or third in any form you can query. At DEBUG it will dump the
tool call inside a wall of JSON you cannot filter or aggregate. Questions 2 and 3
are yours to collect as structured fields, and collecting them is the
callback-or-plugin job. So the rule is **in addition to the framework logger, not
instead of it.**

**The per-agent callback.** The same hook points exist on a single agent. Instead
of a plugin class, you attach a function:

```python
import logging

telemetry = logging.getLogger("agent.telemetry")   # your namespace, not google_adk

def log_tool(tool, args, tool_context):
    telemetry.info("tool_call", extra={
        "event": "tool_call",
        "tool": tool.name,
        "tool_args": args,
        "agent": tool_context.agent_name,
    })
    return None   # return a value instead to block or replace the call

root_agent = Agent(..., before_tool_callback=log_tool)
```

`getLogger("agent.telemetry")` returns a logger under a name you choose; the name
is arbitrary and unrelated to ADK. It matters for two reasons: you can set its
level and attach handlers by that same name in your logging config, and the name
rides on every record, so in Cloud Logging you can filter to `agent.telemetry`
and see your events without the framework's. Keeping it out of the `google_adk`
tree is what lets you control the two independently.

**Which to use.** The callback and the plugin run the same hooks; they differ in
scope.

| Use a plugin when... | Use a per-agent callback when... |
|---|---|
| you want uniform telemetry across every agent and tool | the logic belongs to one agent only |
| the logging carries state (a timer for latency) or config | you are prototyping and want the fewest lines |
| you want one field schema for downstream BigQuery or Looker analysis | you need to block or rewrite a step for that one agent |

A plugin registers once on the `App` and fires everywhere, which is why it is the
right default for production telemetry: one place, one schema, every agent. A
per-agent callback is siloed by design; with several agents the same logging
drifts across them and you cannot see the whole app at once. Reach for it when
the logic is genuinely local, or when you want a hook to **short-circuit**:
returning a value from a `before_*` callback stops or replaces the step, which
turns the same hook into a guardrail. Note that both callbacks and plugins run in
the request thread, so keep the work cheap and let the logging handler do the
shipping.

**The takeaway.** Set a level on ADK's logger to answer framework questions, add
a plugin (or, for one agent, a callback) to answer the tool and cost questions
ADK cannot, and route both through one logging config so every agent produces the
same queryable record.

## Part 5: a custom server where you own every stream

**Why you are here.** You are not using `adk web`, `adk api_server`, or ADK's
`get_fast_api_app` helper. You have a hand-written FastAPI service (a common
situation once you need custom routes, auth, or streaming), and you want to
configure all four streams in one place. Note that `get_fast_api_app` has no
`log_level` parameter either, so owning the logging config is the norm for any
custom server, not an edge case.

[examples/06_custom_server.py](examples/06_custom_server.py) is a complete,
minimal server built on current ADK 2.x idioms. The shape to copy:

```python
# Build an App with your plugins, hand it to a Runner, close it on shutdown.
adk_app = App(name="custom_server", root_agent=root_agent,
              plugins=[StructuredTelemetryPlugin()])   # the Part 4 plugin

@asynccontextmanager
async def lifespan(app):
    app.state.runner = Runner(app=adk_app, session_service=InMemorySessionService())
    yield
    await app.state.runner.close()      # releases plugin/toolset resources
```

Passing `app=` to the `Runner` is the recommended ADK 2.x form; passing
`plugins=` to the `Runner` still works but is deprecated. For logging, a single
`dictConfig` at startup is the clean way to set up every stream at once: your JSON
telemetry logger, the `google_adk` group's level, the root handler, and the
`uvicorn.access` filter from Part 2. It is also where you tame framework noise
with a truncating filter, so one runaway DEBUG line cannot blow out your log:

```python
class TruncateFilter(logging.Filter):
    def __init__(self, max_length=200):
        super().__init__(); self.max_length = max_length
    def filter(self, record):
        msg = record.getMessage()
        if len(msg) > self.max_length:
            record.msg = msg[: self.max_length] + " ...[truncated]"
            record.args = ()
        return True
```

**Do this.**

```bash
.venv/bin/python examples/06_custom_server.py
# in another terminal:
curl -s -X POST localhost:8080/chat -H 'content-type: application/json' \
     -d '{"message":"weather in Tokyo?"}'
```

**You will see** the structured telemetry from your Part 4 plugin on the server's
stdout, followed by the HTTP response to the client:

```console
{"severity": "INFO", "message": "tool_start", "tool": "get_weather", "tool_args": {"city": "Tokyo"}}
{"severity": "INFO", "message": "tool_end", "tool": "get_weather", "latency_ms": 0.6, "status": "ok"}
{"response": "The weather in Tokyo is currently 27°C and humid."}
```

**What it means.** One process, all four streams under your control in one config
block, and the same structured events you designed in Part 4 now flowing out of a
real HTTP server. This server is what Part 6 containerizes and ships.

## Part 6: Cloud Run

**Why you are here.** In 1.5 you deployed a server to Cloud Run and got its logs
into Cloud Logging for free, but as raw text with the wrong severity. Now you fix
that: you want the logs to be first-class, correct severity, and grouped by
request. Cloud Run's contract makes the ingestion part free, **anything a
container writes to stdout/stderr is ingested into Cloud Logging automatically**,
no sink to install. Your only job is to make each line a good JSON object. Two
Cloud Run facts decide how.

**Fact one: severity lives in the JSON, not in the stream, and Cloud Run's guess
is unreliable.** You saw in 1.4 and 1.5 that Cloud Run does *not* reliably map a
stream to a severity: the plain `INFO -` lines your agent wrote to **stderr**
landed as **Default** severity, not the level they claimed. (The commonly cited
rule is that stderr reads as **ERROR** on Cloud Run, and ADK's own source works
around it, its comment says LiteLLM's stderr loggers are redirected to stdout
"because in cloud environments like GCP, stderr output is treated as ERROR
severity regardless of the actual log level." In our runs the lines came through
as Default instead. Either way the point holds: the severity you get from the
stream is a guess, and it is not the level you logged at.) The fix is the same
regardless of which guess your environment makes: write JSON to stdout with an
explicit `severity` field, and stop leaving it to inference.

**Fact two: correlate every stream by trace.** Cloud Run sets an
`X-Cloud-Trace-Context` header on each request. If you put it into the special
`logging.googleapis.com/trace` field, formatted as
`projects/PROJECT_ID/traces/TRACE_ID`, the Logs Explorer groups every line of one
request together, across all four streams.

[examples/07_cloudrun_json.py](examples/07_cloudrun_json.py) does both. The clever
part is a `contextvars.ContextVar`: it parses the trace once at the start of each
request, and the formatter reads it for **every** record emitted while that
request is handled, including the deep `google_adk` framework logs you never touch:

```python
current_trace: ContextVar[str | None] = ContextVar("current_trace", default=None)

class CloudRunJsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {"severity": record.levelname, "message": record.getMessage()}
        trace_id = current_trace.get()
        if trace_id and PROJECT_ID:
            entry["logging.googleapis.com/trace"] = f"projects/{PROJECT_ID}/traces/{trace_id}"
        # ... plus any extra= fields from your plugin ...
        return json.dumps(entry, default=str)
```

**Do this**, passing the trace header the way Cloud Run would:

```bash
GOOGLE_CLOUD_PROJECT=your-project .venv/bin/python examples/07_cloudrun_json.py
# in another terminal:
curl -s -X POST localhost:8082/chat \
  -H 'content-type: application/json' \
  -H 'X-Cloud-Trace-Context: 105445aa7843bc8bf206b12000100000/1;o=1' \
  -d '{"message":"weather in San Francisco?"}'
```

**You will see** that your app log, your plugin telemetry, **and** ADK's own
framework log all carry the same trace value:

```console
{"severity": "INFO", "message": "chat_request_received", "logging.googleapis.com/trace": "projects/jwd-gcp-demos/traces/105445aa...", "user_id": "web-user"}
{"severity": "INFO", "message": "llm_request", "logging.googleapis.com/trace": "projects/jwd-gcp-demos/traces/105445aa...", "agent": "weather_agent"}
{"severity": "INFO", "message": "Sending out request, model: gemini-3.7-flash...", "logging.googleapis.com/trace": "projects/jwd-gcp-demos/traces/105445aa..."}
```

**What it means.** That third line is a framework log you did not write, and it
still carries the trace, because the `ContextVar` threads it through everything
that runs during the request. In the Logs Explorer, clicking that trace shows all
three lines grouped as one request, so you can read a single request's whole
lifecycle across all four streams without hunting for the lines that belong to it.

### 6.1 Deploying, and what to check afterwards

```bash
export PROJECT_ID=your-project REGION=us-central1
./deploy/deploy_cloudrun.sh
```

The script deploys `demo_agent` with `adk deploy cloud_run`, then runs one real
turn against the result. It fails loudly if the service is not `Ready` or if that
turn does not return 200, because a Cloud Run deploy can report success and still
be broken (see the traps below).

#### Testing the deployed service

Same two-step flow as [1.3](#13-the-same-dial-on-adk-api_server), pointed at the
service URL instead of localhost. The deploy answers "allow unauthenticated", so
no token is needed:

```bash
URL=$(gcloud run services describe adk-logging-demo \
        --region="$REGION" --format='value(status.url)')

curl -s -X POST "$URL/apps/demo_agent/users/u1/sessions/s1" \
     -H 'content-type: application/json' -d '{}'

curl -s -X POST "$URL/run" \
     -H 'content-type: application/json' \
     -d '{"app_name":"demo_agent","user_id":"u1","session_id":"s1",
          "new_message":{"role":"user","parts":[{"text":"What'\''s the weather in Tokyo?"}]}}'
```

If you deployed privately instead, add `-H "authorization: Bearer $(gcloud auth
print-identity-token)"` to both calls.

Then read what it logged:

```bash
gcloud run services logs read adk-logging-demo --region="$REGION" --limit=25
```

```console
POST 200 https://adk-logging-demo-....run.app/apps/demo_agent/users/u1/sessions/s1
2026-09-03 20:57:58,739 - INFO - api_server.py:1092 - New session created: s1
INFO:     169.254.169.126:48792 - "POST /apps/.../sessions/s1 HTTP/1.1" 200 OK
POST 200 https://adk-logging-demo-....run.app/run
2026-09-03 20:57:58,895 - INFO - google_llm.py:255 - Sending out request, model: gemini-3.7-flash, ...
2026-09-03 20:58:00,412 - INFO - google_llm.py:327 - Response received from the model.
2026-09-03 20:58:00,414 - INFO - agent.py:40 - tool get_weather called for city='Tokyo'
2026-09-03 20:58:00,418 - INFO - google_llm.py:255 - Sending out request, model: gemini-3.7-flash, ...
2026-09-03 20:58:10,044 - INFO - google_llm.py:327 - Response received from the model.
INFO:     169.254.169.126:48806 - "POST /run HTTP/1.1" 200 OK
```

**What it means.** The five-line lifecycle trail from 1.1.1 is intact, unchanged
by deployment. What is new is a *third* line format: `POST 200 https://...` is
Cloud Run's own request log, which exists alongside uvicorn's `INFO:` access line
for the very same request. Stream 3 now has two writers, and neither is the
`--log_level` flag's business.

Now ask Cloud Logging for the severity of that tool line, the problem Part 6
exists to fix:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" textPayload:"tool get_weather"' \
  --limit=1 --format='value(severity,textPayload)'
```

```console
	2026-09-03 20:58:00,414 - INFO - agent.py:40 - tool get_weather called for city='Tokyo'
```

That leading tab is an **empty severity field**. The line says `INFO` in its text,
but Cloud Logging assigned it nothing, so severity filters cannot see it and the
Logs Explorer shows it at default level. Nothing correlates it to a request
either. This is the plain-text baseline the JSON formatter above replaces: emit
`severity` and `logging.googleapis.com/trace` as real fields and both problems go
away.

#### Traps

- `adk deploy cloud_run --log_level ...` sets **gcloud's** own `--verbosity`, not
  the deployed app's level. The generated container runs at **INFO** no matter
  what you pass, so set your app's level in code (the `dictConfig` from Part 5),
  not on the deploy command. (This is the Part 1/Part 2 lesson again: know which
  thing a flag actually configures.)
- Use `--otel_to_cloud`, not the deprecated `--trace_to_cloud`, to export the
  telemetry from Part 7.
- The container's dependencies come from a `requirements.txt` **inside the agent
  folder**, not the one at the project root. Without it ADK writes
  "`# No requirements.txt found.`" into the generated Dockerfile and the image
  ships with `google-adk` alone, so `--otel_to_cloud` crashes the container on
  boot with `ModuleNotFoundError: No module named 'opentelemetry.exporter'`.
- Your model's region is not your service's region. This agent's model lives in
  `global` while the service runs in `us-central1`; if the container resolves the
  wrong one, the deploy *succeeds* and then every `/run` returns 500 wrapping a
  404 for the model. An agent-local `.env` will not fix it: ADK loads that file
  and then re-applies any variable already present in the environment on top of
  it, and Cloud Run already sets `GOOGLE_CLOUD_LOCATION`. Set it as a real Cloud
  Run env var, which is why the script calls `gcloud run services update` after
  deploying.
- `adk deploy` catches gcloud's failure and still exits 0, so `set -e` will not
  catch a failed deploy. Check the service's `Ready` condition, not merely that
  the service exists: a failed deploy leaves the service record behind.

## Part 7: OpenTelemetry GenAI telemetry (stream 4)

**Why you are here.** Everything so far was the `logging` module (streams 1-3).
Stream 4 is separate machinery: ADK emits **OpenTelemetry** spans, one per LLM
call and tool call, plus GenAI events. They never print; they leave through an
exporter. You want them because a span tree tells you *where the latency went* in
a way flat log lines cannot. This is what `adk web --otel_to_cloud` turns on, and
you can drive it yourself.

**Do this** in console mode, which needs no cloud access and just prints the
spans:

```bash
.venv/bin/python examples/08_otel_cloud.py
```

**You will see** the span hierarchy:

```console
"name": "invocation"
  "name": "invoke_agent weather_agent"
    "name": "call_llm"
      "name": "generate_content gemini-3.7-flash"
    "name": "execute_tool get_weather"
    "name": "call_llm"
```

**What it means.** This is the same run you have watched all tutorial, now shown
as nested timed spans: the whole invocation contains the agent, which makes a
first model call, executes the tool, then makes a second model call. Exported to
Cloud Trace, each span carries a duration, so you can see at a glance whether your
latency is in the model or the tool.

**To export it to Google Cloud**, the setup is two calls:

```python
from google.adk.telemetry.google_cloud import get_gcp_exporters
from google.adk.telemetry.setup import maybe_set_otel_providers

hooks = get_gcp_exporters(enable_cloud_tracing=True, enable_cloud_logging=True)
maybe_set_otel_providers([hooks])   # note: a LIST of hooks
```

```bash
.venv/bin/python examples/08_otel_cloud.py cloud
```

Spans land in **Cloud Trace**; GenAI events land in **Cloud Logging** under the
log name `adk-otel`. This mode needs two extra packages, already in
`requirements.txt`: `opentelemetry-exporter-otlp-proto-http` and
`opentelemetry-exporter-gcp-logging`.

### 7.1 The privacy knob you must know about

By default, this telemetry carries **metadata only**; prompt and response text
are elided. One environment variable controls it, and it must be set **before ADK
is imported**:

```bash
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT   # safe default
# other values that DO include content: SPAN_ONLY | EVENT_ONLY | SPAN_AND_EVENT
```

**What it means.** Leave it at `NO_CONTENT` in production unless you have a
specific, reviewed reason to capture prompts and responses, because captured
content then lives in your logging backend under its retention and access rules.
For a one-off, scope it through `RunConfig.telemetry` instead of flipping the
whole process.

> The richest GenAI **content events** ride on ADK's experimental semantic
> conventions, an area the SDK marks as subject to change. The **spans** and the
> setup shown here are stable; treat the exact shape of content events as
> evolving, and pin your `google-adk` version.

## Part 8: Agent Runtime (Vertex AI Agent Engine)

**Why you are here.** Agent Engine is the other place you deploy. You already met
its logging behavior hands-on in 1.6 (deploy the agent object, the platform owns
the format) and 1.7 (deploy your own container, you keep your format). This part
adds the telemetry layer on top of that and states the operational facts once.

What deploying the agent (1.6, native) means in practice:

- You do **not** run uvicorn or write JSON lines. The platform captures the
  container's output and the OTel signals for you.
- **Traces** appear in Cloud Trace automatically. Adding `--otel_to_cloud` exports
  logs and metrics too; under the hood the flag sets
  `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` on the deployed agent.
- Logs land on the `aiplatform.googleapis.com/ReasoningEngine` monitored
  resource. Note the stream: the agent and framework lines are on
  `aiplatform.googleapis.com/reasoning_engine_**stderr**`, not stdout, which
  carries only the web server's access lines (this trips people up, as 1.6
  showed). Read by resource type to catch both.

```bash
export PROJECT_ID=your-project REGION=us-central1
./deploy/deploy_agent_engine.sh
gcloud logging read \
  'resource.type="aiplatform.googleapis.com/ReasoningEngine"
   resource.labels.reasoning_engine_id="ENGINE_ID"' \
  --project="$PROJECT_ID" --limit=20 --format='table(severity,textPayload)'
```

**The reuse that matters.** Your Part 4 structured plugin still works here
unchanged: its records go to stdout and are captured, so you get the same
structured fields on Agent Engine that you get on Cloud Run. The one thing you
drop is the trace-header parsing from Part 6, because the platform handles request
correlation for you. Write the plugin once, use it in three places (local server,
Cloud Run, Agent Engine).

If you scaffold with `agents-cli`, the generated project wires a
`setup_telemetry()` for you and gates a richer prompt-response logging tier on a
`LOGS_BUCKET_NAME` (exported to GCS and BigQuery). That is the same OTel machinery
from Part 7, pre-wired.

## How to choose

| You are... | Use | Why |
|---|---|---|
| Getting the shape of a run | `--log_level INFO` | Lifecycle without contents. |
| Debugging what the model saw | `--log_level DEBUG` | Full prompt, history, tool schema. |
| Reading tool calls live in dev | `LoggingPlugin` (3.1, 3.5) | Clean narration + tokens. Prints, so dev only. |
| Capturing one bad turn in full | `DebugLoggingPlugin` (3.3, 3.5) | Complete YAML record, secrets redacted. |
| Emitting metrics for production | Custom `BasePlugin` (Part 4) | Real `logging` records; queryable, alertable. |
| Logging or guarding one agent only | Per-agent callback (4.1) | Siloed by design; can short-circuit a step. |
| Running your own HTTP server | `dictConfig` + the Part 4 plugin | Own all four streams in one place. |
| Seeing raw logs reach the cloud, fast | Cloud Run Job/service, no JSON (1.4, 1.5) | Zero setup; but severity is Cloud Run's guess (Default), not yours. |
| Deploying to Cloud Run for real | JSON to stdout + trace field (Part 6) | Auto-ingested; severity you set; grouped by request. |
| Deploying the agent to Agent Runtime | `adk deploy agent_engine` (1.6) + `--otel_to_cloud` | Managed; but the platform owns log format/stream. |
| Keeping your own logging on Agent Runtime | Custom container / BYOC (1.7) | Your server, your format; you implement the runtime contract. |
| Finding where latency goes | `--otel_to_cloud` / `get_gcp_exporters` | Timed span tree in Cloud Trace. |

Best-practice summary:

- Serve at **INFO or WARNING** in production; keep DEBUG for active debugging.
- Emit **one JSON object per line** with an explicit **`severity`**, and log to
  **stdout**. Do not rely on Cloud Run inferring severity from the stream: 1.4
  and 1.5 showed plain stderr lines landing as Default, and the common rule says
  ERROR, so set severity yourself.
- Correlate with the **trace** field so a request is one filterable group.
- Keep GenAI content capture at **`NO_CONTENT`** unless you have a reviewed reason.
- Tune the framework as a group via `logging.getLogger("google_adk")`, and
  silence `uvicorn.access` health-check spam.
- Remember which stream a flag configures. Most confusion is a flag aimed at the
  wrong stream.

## Beyond logging

This tutorial stopped at logging and the log-facing side of tracing. The wider
observability story, briefly:

- **Cloud Trace** spans (Part 7) are worth exploring on their own for latency
  breakdowns across `call_llm` and `execute_tool`.
- **BigQuery Agent Analytics** (`BigQueryAgentAnalyticsPlugin`) logs structured
  agent events to BigQuery for conversational analytics and LLM-as-judge evals.
- **Third-party platforms** (AgentOps, Phoenix, MLflow, Weave, and others)
  integrate over OpenTelemetry for session replays and dashboards.

The ADK observability skill and `https://adk.dev/observability/` cover these.

## Verification status

Verified by running end to end against a real project (`jwd-gcp-demos`, Vertex
AI, Gemini 3.7 Flash):

- Examples 01 through 08 all run; every console block above is captured from a
  real run.
- Part 1's DEBUG/INFO/WARNING differences, Part 3's plugin narration, Part 4's
  JSON events, Part 5's server, and Part 6's trace correlation are all reproduced
  as shown.
- Example 08 `cloud` mode exports to Cloud Trace and Cloud Logging without error
  via application-default credentials.
- The **cloud deploys in 1.4-1.7 were all run** against `jwd-gcp-demos`
  (2026-09-03) and every console block in those sections is captured from the
  real run: the Cloud Run Job (1.4), the Cloud Run service (1.5), the native
  Agent Runtime agent (1.6), and the custom container / BYOC (1.7). The findings
  that differ from common advice, stderr landing as Default not ERROR (1.4/1.5),
  the platform owning log format on native Agent Runtime (1.6), the project-level
  `artifactregistry.reader` and reserved-var model-region traps (1.7), are all
  from those runs.
- The **plugin Cloud Run Jobs in 3.2, 3.4, and 4 were run** against `jwd-gcp-demos`
  (2026-09-03) with [deploy/deploy_plugin_job.sh](deploy/deploy_plugin_job.sh).
  3.2's two findings (the narration survives `LOG_LEVEL=WARNING` untouched; it
  lands on stdout with Default severity and literal ANSI bytes) and 3.4's (the
  YAML is discarded with the container until a Cloud Storage volume is mounted,
  and the plugin then emits its mode-600 warning against the FUSE mount) are both
  from those runs. Part 4's Job confirmed the structured payoff: the plugin's JSON
  parsed into queryable `jsonPayload` fields (`event`, `tool`, `latency_ms`,
  `status`) and its `severity` landed as `INFO`, not Default.

Not verified here (documented, run them yourself):

- The Part 6/7 `deploy/deploy_cloudrun.sh` structured-JSON deploy and the
  `--otel_to_cloud` telemetry export end to end. The 07 formatter and trace
  correlation are verified locally (Part 6 body); the containerized deploy of it
  is not.
- Reading the exported `adk-otel` entries back with `gcloud logging read`
  (needs an interactive `gcloud auth login` in your shell).

## References

- [ADK logging](https://adk.dev/observability/logging/) — log levels, the
  `google_adk` tree, content-capture env var.
- [ADK observability overview](https://adk.dev/observability/) — logging,
  tracing, metrics, integrations.
- [Cloud Trace for ADK](https://adk.dev/integrations/cloud-trace/) — the span
  hierarchy and per-deployment setup.
- [Structured logging on Cloud Run](https://cloud.google.com/run/docs/logging) —
  the special JSON fields (`severity`, `logging.googleapis.com/trace`) Cloud
  Logging parses.
- [Agent Engine observability](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/manage/tracing) —
  where Reasoning Engine logs and traces land.
