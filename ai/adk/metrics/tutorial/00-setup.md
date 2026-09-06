[→ Scenarios](scenarios.md)<br>
[Tutorial index](../TUTORIAL.md)

---

# Setup

All commands run from this folder. Do this once. Part 1 needs only a model;
Parts 2 to 4 add Google Cloud APIs, which this page enables now so you do not
stop later.

## Create the environment

```bash
cd ai/adk/metrics
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Point the agent at a model

Copy `.env.example` to `.env`. On GCP the simplest path is Vertex AI with your
existing `gcloud` credentials:

```bash
cp .env.example .env
# edit .env to contain:
#   GOOGLE_GENAI_USE_VERTEXAI=TRUE
#   GOOGLE_CLOUD_PROJECT=your_project_id
#   GOOGLE_CLOUD_LOCATION=global
gcloud auth application-default login   # if you have not already
```

## Set your shell variables

The cloud parts read your project and region, and the metrics resource labels,
from shell variables. Set them once in a file you `source`.

```bash
cp env.sh.example env.sh
# edit env.sh: set PROJECT_ID to your real project
source env.sh
```

`env.sh` is gitignored. **`source env.sh` again in each new terminal**, since
variables do not cross terminals.

## Enable the APIs (Parts 2 to 4)

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

Two latencies are the whole reason the tool and token distributions have shape.
The tools are wrapped in a `StatusAwareTool`, a `FunctionTool` subclass that
reports a failure status to telemetry so [1.3](part-1/1.3-attributes-and-cardinality.md)
can show a failing tool split its metric.

```python
class StatusAwareTool(FunctionTool):
    def _detect_error_in_response(self, response):
        if isinstance(response, dict) and response.get("status") == "error":
            return "no_data"
        return None
```

## Verify it runs

```bash
.venv/bin/python examples/01_console_metrics.py
```

**Expected output:** the agent's answer, then six metric names. If you see the
histograms, your model and environment are set. [Scenarios](scenarios.md)
explains the controlled experiments the pages run; [Part 1](part-1/index.md)
starts reading them.

---

[→ Scenarios](scenarios.md)<br>
[Tutorial index](../TUTORIAL.md)
