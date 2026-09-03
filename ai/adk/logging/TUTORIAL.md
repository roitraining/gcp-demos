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

The script from 1.1 runs once and exits; it serves no HTTP. The honest way to
run it on Cloud Run is therefore a **Job**, not a service (a service would fail
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
*service*.) The lesson is the same either way: **do not assume the severity of a
plain line, check it**, because Cloud Run's guess is not reliably what you want.

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
This is the practical meaning of "you deploy the agent, not the server."

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
by level, exactly as it was on Cloud Run and on your laptop. So the scorecard for
native Agent Runtime is: **level, yours** (via `LOG_LEVEL`); **format, stream, and
severity, the platform's.** Severity, incidentally, is blank/Default here too, the
same limitation as Cloud Run, and the same reason Part 6 exists. This shapes what
carries over from Part 4: the structured plugin you build there still works here
(its records go through whatever handler the platform installed, and its `extra=`
fields survive), but any formatting you try to impose from your own `dictConfig`
will not.

> Two traps. First, `adk deploy agent_engine` **creates a new reasoning engine on
> every deploy**; it does not update in place, so the WARNING redeploy has a new
> `ENGINE_ID`. Delete the old ones when you are done (the deploy script prints the
> teardown command). Second, `adk deploy` exits 0 even when the underlying deploy
> failed, so the query is the real success check, not the exit code.

### 1.7 The same server as a custom container on Agent Runtime

**Why you are here.** 1.6 deployed the agent object and let the platform serve it.
But Agent Runtime also accepts a **container you build yourself** (bring your own
container), which is how you run 1.5's kind of hand-written server on the managed
platform instead of on Cloud Run. The catch, and the whole lesson of this
section, is that the platform's contract constrains what that container must be.

A custom container on Agent Runtime is not free-form. The runtime contract
requires it to listen on **port 8080** and implement two specific routes,
`POST /api/reasoning_engine` (unary) and `POST /api/stream_reasoning_engine`
(streaming), each taking a `{"class_method", "input"}` body. A plain `/chat`
route like 1.5's is therefore not enough on its own. The smallest server that
satisfies the contract wraps the agent in `vertexai.agent_engines.AdkApp` and
dispatches the named method to it; that is what
[agent_runtime_byoc/main.py](agent_runtime_byoc/main.py) does, in about ninety
lines. Its logging is deliberately the same naive Part 1 config as 1.5, so the
question this section answers is: with *your own* container, do you get your
logging back, or does the platform still override it?

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
trap. So the choice between the two Agent Runtime deploys is really a choice about
logging: take the managed agent object and accept the platform's format (1.6), or
run your own container and keep your own (1.7). Severity is still Default in both;
that is Part 6's problem regardless of which you pick.

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
stream. Silencing health-check spam this way is a high-value, low-effort change
to a deployed agent. It also sets up the rest of this tutorial: to control agent
logging well, you stop relying on a global level and start configuring each
stream deliberately.

## Part 3: a readable narration of the agent's steps

**Why you are here.** INFO is too terse to debug a tool-calling problem (it tells
you a request happened, not what the tool was called with), and DEBUG is a wall
of raw JSON. In development you often want the middle ground: a clean,
human-readable narration of the agentic steps, which tool ran, with which
arguments, what it returned, how many tokens it cost, without writing that
yourself. ADK ships two plugins for exactly this.

### 3.1 LoggingPlugin: one line to wire up

A plugin attaches to the `App`. That is the whole setup, shown in
[examples/03_logging_plugin.py](examples/03_logging_plugin.py):

```python
from google.adk.apps.app import App
from google.adk.plugins import LoggingPlugin

app = App(name="demo", root_agent=root_agent, plugins=[LoggingPlugin()])
```

**Do this.**

```bash
.venv/bin/python examples/03_logging_plugin.py
```

The example asks *"What's the weather in London?"* **You will see** a narrated
lifecycle (trimmed here to the interesting middle):

```console
[logging_plugin] 🧠 LLM RESPONSE
[logging_plugin]    Content: function_call: get_weather
[logging_plugin]    Token Usage - Input: 140, Output: 5
[logging_plugin] 🔧 TOOL STARTING
[logging_plugin]    Tool Name: get_weather
[logging_plugin]    Arguments: {'city': 'London'}
[logging_plugin] 🔧 TOOL COMPLETED
[logging_plugin]    Result: {'status': 'ok', 'report': 'The weather in London is 15C and drizzling.'}
```

**What it means.** In one glance you can see the model chose to call `get_weather`
with `{'city': 'London'}`, what came back, and that the deciding model call cost
140 input and 5 output tokens. This is the view you want when a tool is being
called with the wrong arguments, or not called when it should be, and you do not
want to parse DEBUG to find out. Compare it to the DEBUG output from Part 1: same
information about the tool call, far less noise.

> **The catch that decides where you use it.** `LoggingPlugin` writes with
> `print()` and ANSI color codes, **not** through the `logging` module. That is
> perfect in a terminal and wrong for a deployed service: it ignores your
> handlers, levels, and formatters, and the color bytes corrupt a JSON log line.
> Use it for local debugging. When you need this information *in production*, you
> use Part 4 instead, which is the whole reason Part 4 exists.

### 3.2 DebugLoggingPlugin: capture one whole turn to a file

**Why.** Sometimes one specific turn misbehaves and you want the complete,
inspectable record to diff or attach to a bug report, not a stream you have to
watch live.

```python
from google.adk.plugins import DebugLoggingPlugin
plugin = DebugLoggingPlugin(output_path="adk_debug.yaml")
```

**Do this**, then open the file it writes:

```bash
.venv/bin/python examples/04_debug_plugin.py
cat adk_debug.yaml
```

**You will see** one YAML document per invocation:

```console
- timestamp: '2026-08-31T20:05:03.639120'
  entry_type: llm_request
  data:
    model: gemini-3.7-flash
    contents:
    - role: user
      parts:
      - text: What's the weather in a city you don't know, like Paris?
```

**What it means.** It is the full turn on disk: exact prompt, system instruction,
tool arguments, tool results, token counts, and session state. Credentials and
`temp:` state are redacted, and the file is created readable only by you
(`0600`). Treat it as sensitive, it holds full prompt content by design. This is
a debugging capture, not a log sink you leave running.

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

**What it means.** Every line is now a machine-readable event. You can compute
average model latency, sum token usage per session for cost, alert when a tool's
`status` is `error`, or filter to one tool, all with log queries, because these
are structured fields and not prose. And nothing here is terminal-specific: swap
the formatter and the exact same events become Cloud Logging entries in Part 6.

Two things this example teaches by doing:

- **Reserved field names.** Keys in `extra=` must not collide with built-in
  `LogRecord` attributes (`args`, `name`, `message`, `module`). The example uses
  `tool_args`, not `args`, precisely because `args` collides and raises a
  `KeyError` inside the log call. (This one bites everyone once.)
- **Plugin vs. callback.** A plugin is app-wide: it fires for every agent and
  every tool. If you only care about one agent or tool, the surgical alternative
  is a per-agent callback, for example `Agent(..., before_tool_callback=my_fn)`.
  Reach for a plugin when you want uniform telemetry across the whole app.

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
three lines grouped as one request. For debugging a production agent, this
correlation earns its keep faster than any other change here.

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

Now the reason Part 6 exists. Ask Cloud Logging for the severity of that tool line:

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
| Reading tool calls live in dev | `LoggingPlugin` | Clean narration + tokens. Prints, so dev only. |
| Capturing one bad turn in full | `DebugLoggingPlugin` | Complete YAML record, secrets redacted. |
| Emitting metrics for production | Custom `BasePlugin` (Part 4) | Real `logging` records; queryable, alertable. |
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
