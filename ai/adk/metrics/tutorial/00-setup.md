[→ Scenarios](scenarios.md)<br>
[Tutorial index](../TUTORIAL.md)

---

# Setup

All commands run from `ai/adk/metrics`. Do this once. Part 1 needs only a model;
Parts 2 to 4 add Google Cloud APIs, which this page enables now so you do not
stop later.

## Create the environment

From the repo root:

**Command:**

```bash
cd ai/adk/metrics
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Point the agent at a model

Copy the example file:

**Command:**

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

**Command:**

```bash
gcloud auth application-default login
```

## Set your shell variables

The cloud parts read your project and region, and the metrics resource labels,
from shell variables. Copy the template:

**Command:**

```bash
cp env.sh.example env.sh
```

Open `env.sh` in your editor and set `PROJECT_ID` to the same project id as in
`.env`. `env.sh` also exports `GOOGLE_CLOUD_PROJECT` from it, and when both are
set, the shell value wins over `.env`. Then source it:

**Command:**

```bash
source env.sh
```

`env.sh` is gitignored. **`source env.sh` again in each new terminal**, since
variables do not cross terminals.

## Enable the APIs (Parts 2 to 4)

**Command:**

```bash
gcloud services enable \
  telemetry.googleapis.com \
  monitoring.googleapis.com \
  bigquery.googleapis.com \
  bigquerystorage.googleapis.com
```

The metrics pipeline writes through `telemetry.googleapis.com` and you read back
through `monitoring.googleapis.com`. BigQuery and its Storage Write API are for
[Part 4](part-4/index.md).

## Meet the agent

Every example shares one agent, [demo_agent/agent.py](../demo_agent/agent.py): a
weather assistant with two tools of deliberately different latency.

- `get_weather(city)` is instant and knows four cities. An unknown city returns a
  failure status without raising.
- `get_forecast(city, days)` sleeps 0.3–1.5 s and returns more text.

The two tools give later scenarios a second latency to vary. The tools are
wrapped in a `StatusAwareTool`, a `FunctionTool` subclass that reports a failure
status to telemetry, so [1.3](part-1/1.3-attributes-and-cardinality.md) can show
a failing tool split its metric.

## Verify it runs

**Command:**

```bash
.venv/bin/python examples/01_console_metrics.py
```

The agent's answer prints to the console, and the script writes the metrics JSON
to `out/metrics.json`. Open it in your editor to read it; the dump is too long for
the terminal. In VS Code:

```bash
code out/metrics.json
```

**Expected output:** the answer prints, then the file holds all six metric names.

```console
(metrics written to out/metrics.json)

AGENT: The weather in London is currently 15°C and drizzling.
```

Contents of `out/metrics.json`, trimmed to the first metric and a few of its
fields:

```json
{
    "resource_metrics": [
        {
            "resource": { "attributes": {
                "service.instance.id": "laptop-1",
                "cloud.region": "us-central1",
                "service.name": "adk-metrics"
            } },
            "scope_metrics": [
                {
                    "scope": { "name": "gcp.vertex.agent", "version": "2.8.0" },
                    "metrics": [
                        {
                            "name": "gen_ai.execute_tool.duration",
                            "unit": "s",
                            "data": { "data_points": [ {
                                "attributes": {
                                    "gen_ai.agent.name": "weather_agent",
                                    "gen_ai.tool.name": "get_weather",
                                    "gen_ai.tool.type": "StatusAwareTool"
                                },
                                "count": 1,
                                "sum": 0.002
                            } ] }
                        }
                    ]
                }
            ]
        }
    ]
}
```

> [!TIP]
> Leave `out/metrics.json` open in your editor. Later steps rewrite this same
> file each run, so the pane refreshes with the new results in place.

If you see the answer and the file, your model and environment are set. A
`403 PERMISSION_DENIED` on `your_project` instead means `env.sh` still holds the
placeholder, and its `GOOGLE_CLOUD_PROJECT` is overriding `.env`. Set
`PROJECT_ID` in `env.sh` and source it again. [Part 1](part-1/index.md) walks
through what these fields mean.

---

[→ Scenarios](scenarios.md)<br>
[Tutorial index](../TUTORIAL.md)
