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

The cloud parts read your project and region, and the metrics resource labels,
from shell variables. Copy the template:

```bash
cp env.sh.example env.sh
```

Open `env.sh` in your editor and set `PROJECT_ID` to your real project id, then
source it:

```bash
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
            return "lookup_failed"
        return None
```

## Verify it runs

```bash
.venv/bin/python examples/01_console_metrics.py
```

**Expected output:** the agent's answer prints to the console, and the metrics
JSON is written to `out/metrics.json` (a full dump is too long to read in a
terminal). Open it in your editor:

```console
AGENT: The weather in London is currently 15°C and drizzling.
(metrics written to out/metrics.json)
```

The file holds all six metric names. Cut here to the first metric:

```json
{
    "resource_metrics": [
        {
            "resource": { "attributes": { "service.name": "adk-metrics" } },
            "scope_metrics": [
                {
                    "scope": { "name": "gcp.vertex.agent", "version": "2.8.0" },
                    "metrics": [
                        {
                            "name": "gen_ai.execute_tool.duration",
                            "unit": "s",
                            "data": { "data_points": [ {
                                "attributes": { "gen_ai.agent.name": "weather_agent" },
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

If you see the answer and the file, your model and environment are set. A
`403 PERMISSION_DENIED` on `your_project` instead means a shell variable is
overriding `.env`; run `unset GOOGLE_CLOUD_PROJECT` and try again, or fix
`env.sh`. [Part 1](part-1/index.md) walks through what these fields mean.

---

[→ Scenarios](scenarios.md)<br>
[Tutorial index](../TUTORIAL.md)
