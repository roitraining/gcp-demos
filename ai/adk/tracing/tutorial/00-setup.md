[→ Scenarios](scenarios.md)<br>
[Tutorial index](../TUTORIAL.md)

---

# Setup

All commands run from this folder. Do this once. Part 1 needs only a model;
Parts 2 to 4 add Google Cloud APIs, which this page enables now so you do not
stop later.

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
source it:

```bash
source env.sh
```

`OTEL_SERVICE_NAME` becomes the **OpenTelemetry service** filter and the
**Service/workload** column in Trace Explorer, so every laptop run files under a
name you can find. `env.sh` is gitignored. **`source env.sh` again in each new
terminal**, since variables do not cross terminals.

## Enable the APIs (Parts 2 to 4)

```bash
gcloud services enable \
  telemetry.googleapis.com \
  cloudtrace.googleapis.com \
  logging.googleapis.com
```

Spans are written through `telemetry.googleapis.com` and you read them back
through `cloudtrace.googleapis.com`. `logging.googleapis.com` carries the log
side of a trace, which [Part 3](part-3/index.md) correlates.

You also need the roles that let you write and read telemetry. To write spans,
`roles/telemetry.writer` (or `roles/telemetry.tracesWriter` for traces alone).
To read, `roles/cloudtrace.user` and `roles/logging.viewer` — and the second is
what makes the **Logs & Events** tab fill in Part 3. As project owner you already
have these.

## Meet the agent

Every example shares one agent, [demo_agent/agent.py](../demo_agent/agent.py): a
weather assistant with two tools of deliberately different latency.

- `get_weather(city)` is instant and knows four cities. An unknown city returns a
  failure status without raising, and logs a WARNING.
- `get_forecast(city, days)` calls a helper that sleeps 0.3–1.5 s and logs one
  INFO line, so its span owns real time.

Two latencies are the whole reason the tree has shape. Three env gates, all off
by default so the tree is pure ADK, let the one agent show every span shape the
tutorial teaches: `TUTORIAL_CUSTOM_SPAN` (a span inside the forecast tool, 1.6),
`TUTORIAL_CLASSIFY_ERRORS` (turn a failed tool's span red, 1.4), and
`TUTORIAL_RAISE_ON_UNKNOWN` (make the tool raise, 1.4).

## Verify it runs

```bash
.venv/bin/python examples/01_console_spans.py
```

**Expected output:** the agent's answer prints to the console, and the span tree
is written to `out/spans.json` (a full dump is too long to read in a terminal):

```console
AGENT: The weather in London is currently 15°C and drizzling.
(spans written to out/spans.json)
```

If you see the answer and the file, your model and environment are set. A
`403 PERMISSION_DENIED` on `your_project` instead means a shell variable is
overriding `.env`; run `unset GOOGLE_CLOUD_PROJECT` and try again, or fix
`env.sh`. [Part 1](part-1/index.md) reads what is in that file.

---

[→ Scenarios](scenarios.md)<br>
[Tutorial index](../TUTORIAL.md)
