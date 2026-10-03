[→ Scenarios](scenarios.md)<br>
[Tutorial index](../TUTORIAL.md)

---

# Setup

All commands run from this folder. Do this once. Part 1 needs only a model;
Parts 2 to 4 add Google Cloud APIs, which this page enables now so you do not
stop later. You need Python 3.13, the `gcloud` CLI, and `jq`.

## Create the environment

```bash
cd ai/adk/tracing
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Point the agent at a model

Copy the example file:

```bash
cp .env.example .env
```

Open `.env` in your editor and set the values. On GCP the simplest path is
Vertex AI with your existing `gcloud` credentials:

```
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
```

If you have not authenticated before, log in once:

```bash
gcloud auth application-default login
```

## Set your shell variables

The cloud parts read your project, region, and the OpenTelemetry service name
from shell variables. Copy the template:

```bash
cp env.sh.example env.sh
```

Open `env.sh` in your editor and set `PROJECT_ID` to your real project id, then
source it and make that project gcloud's default:

```bash
source env.sh
gcloud config set project "$PROJECT_ID"
```

Several commands in this tutorial, such as `gcloud services enable` below, act
on gcloud's default project when they have no `--project` flag.

`OTEL_SERVICE_NAME` becomes the **OpenTelemetry service** filter and the
**Service/workload** column in Trace Explorer, so every laptop run files under a
name you can find. `env.sh` is gitignored. **`source env.sh` again in each new
terminal**, since variables do not cross terminals.

Unset any `OTEL_EXPORTER_OTLP_*` variables left in your shell. ADK adds an
exporter when they are set, so the local Part 1 scripts would send spans there.

## Enable the APIs

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  telemetry.googleapis.com \
  cloudtrace.googleapis.com \
  logging.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

| API | Used for |
|---|---|
| `aiplatform.googleapis.com` | The Gemini model (every part) and Agent Runtime ([2.4](part-2/2.4-agent-runtime.md)) |
| `telemetry.googleapis.com` | Writing spans |
| `cloudtrace.googleapis.com` | Reading spans back |
| `logging.googleapis.com` | The log side of a trace, which [Part 3](part-3/index.md) correlates |
| `run.googleapis.com`, `cloudbuild.googleapis.com`, `artifactregistry.googleapis.com` | Building and deploying the Cloud Run service ([2.2](part-2/2.2-cloud-run.md)) |

You also need the roles that let you write and read telemetry. To write spans,
`roles/telemetry.writer` (or `roles/telemetry.tracesWriter` for traces alone).
To read, `roles/cloudtrace.user` and `roles/logging.viewer`. The second is
what makes the **Logs & Events** tab fill in Part 3. As project owner you already
have these.

## Meet the agent

Every example shares one agent, [demo_agent/agent.py](../demo_agent/agent.py): a
weather assistant with two tools of deliberately different latency.

- `get_weather(city)` is instant and knows four cities. An unknown city returns a
  failure status without raising, and logs a WARNING.
- `get_forecast(city, days)` calls a helper that sleeps 0.3–1.5 s and logs one
  INFO line, so its span owns real time.

ADK builds the tree; the two latencies make the slow step visible in it. Three
env gates, all off by default so the tree is pure ADK, let the one agent show
every span shape the tutorial teaches. Each is on only when set to `1`:
`TUTORIAL_CUSTOM_SPAN` (a span inside the forecast tool, 1.6),
`TUTORIAL_CLASSIFY_ERRORS` (turn a failed tool's span red, 1.4), and
`TUTORIAL_RAISE_ON_UNKNOWN` (make the tool raise, 1.4).

## Verify it runs

**Command:**

```bash
.venv/bin/python examples/01_console_spans.py
```

**Expected output:** the file path prints at startup, then the agent's answer.
The span tree is written to `out/spans.json` (a full dump is too long to read in
a terminal):

```console
(spans written to out/spans.json)

AGENT: The weather in London is currently 15°C and drizzling.
```

Every run also prints `UserWarning: [EXPERIMENTAL] feature
FeatureName.JSON_SCHEMA_FOR_FUNC_DECL is enabled.` It is harmless for traces.

If you see the answer and the file, your model and environment are set. A
`403 PERMISSION_DENIED` on `your-project-id` instead means a shell variable is
overriding `.env`; run `unset GOOGLE_CLOUD_PROJECT` and try again, or fix
`env.sh`. [Part 1](part-1/index.md) reads what is in that file.

---

[→ Scenarios](scenarios.md)<br>
[Tutorial index](../TUTORIAL.md)
