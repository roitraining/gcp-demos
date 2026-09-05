# Part 6 · Agent Runtime

*The telemetry layer on Vertex AI Agent Engine, and what plugin code carries over.*

> [!NOTE]
> **Why you are here.** Agent Engine is the other place you deploy. You already met
> its logging behavior hands-on in 1.6 (deploy the agent object, the platform owns
> the format) and BYOC (deploy your own container, you keep your format). This
> part adds the telemetry layer on top of that and states the operational facts
> once.

What deploying the agent (1.6, native) means in practice:

- You do **not** run uvicorn or write JSON lines. The platform captures the
  container's output and the OTel signals for you.
- Logs land on the `aiplatform.googleapis.com/ReasoningEngine` monitored
  resource. Note the stream: the agent and framework lines are on
  `aiplatform.googleapis.com/reasoning_engine_**stderr**`, not stdout, which
  carries only the web server's access lines (this trips people up, as 1.6
  showed). Read by resource type to catch both.

**The reuse that matters.** Your Part 4 structured plugin still works here
unchanged: its records go to stdout and are captured, so you get the same
structured fields on Agent Engine that you get on Cloud Run. The one thing you
drop is the trace-header parsing from Part 4, because the platform handles request
correlation for you. Write the plugin once, use it in three places (local server,
Cloud Run, Agent Engine).

The rest of this part is the **telemetry** layer — stream 4 from Part 5, on Agent
Runtime. Unlike Cloud Run, there is no `--otel_to_cloud` flag reaching a server
process here; telemetry is governed by one env var on the deployment, and every
tool is just a different way to write it.

---

### 6.1 One switch, two ways to set it

Telemetry (logs, traces, and metrics) on Agent Runtime is governed by a single
environment variable on the deployment:
**`GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY`**. The `AdkApp` wrapper reads it at
startup — `true` turns telemetry on, `false` off, and anything else (including
the literal `unspecified` the SDK injects when you set nothing) leaves it to the
platform.

From this folder there are two ways to write it, and **they are not
equivalent**:

| Route | What it writes | Source |
|---|---|---|
| **The flag** — `adk deploy agent_engine --otel_to_cloud` | `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` **and** `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` (the span knob, set safe for you) | `cli/cli_deploy.py:1273-1282` |
| **A `.env` line** — `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` in the agent's `.env`, no flag | just that one variable; **the CLI sets no content knobs** | `cli/cli_deploy.py:1283-1291` |

The difference is the content knobs. The flag sets the span knob to `false` for
you; the `.env` route sets nothing else, so on that route **you** add the knobs,
or prompt text ships in the telemetry. 6.2 and 6.3 show each route and read the
deployment's env list back to prove what each one wrote.

If you set neither, the SDK sends `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=unspecified`
and the platform decides. Do not rely on a default — set it explicitly. (Two
other routes exist but this part does not run them: `agent_engines.update(config={"env_vars": …})`
via the `vertexai` SDK, and the Cloud Console toggle.)

> [!NOTE]
> **BYOC.** If you deploy your own container (`agent_runtime_byoc/`), the same
> env var governs its `AdkApp` — **if your deploy passes it.** The BYOC deploy
> script here passes only project/location/log-level today, so telemetry is off
> on that path until you add the variable. Not run here.

---

### 6.2 Deploy A: the flag

Deploy with `--otel_to_cloud` and capture the engine id (the script prints it on
a final `ENGINE_ID=` line).

**Command:**

```bash
source env.sh
export ENGINE_ID=$(./deploy/deploy_agent_engine.sh | sed -n 's/^ENGINE_ID=//p')
```

**Read the deployment's env list.** This is what proves the flag wrote both
variables. `gcloud ai` has no reasoning-engine subcommand in every install, so
read the env list with the `vertexai` SDK:

**Command:**

```bash
.venv/bin/python - "$ENGINE_ID" <<'PY'
import sys, vertexai
c = vertexai.Client(project="$GOOGLE_CLOUD_PROJECT", location="$REGION")
e = c.agent_engines.get(
    name=f"projects/$GOOGLE_CLOUD_PROJECT/locations/$REGION/reasoningEngines/{sys.argv[1]}"
)
for ev in e.api_resource.spec.deployment_spec.env:
    print(f"{ev.name}={ev.value}")
PY
```

**Expected output** — the flag added the last two lines:

```console
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_LOCATION=global
LOG_LEVEL=info
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false
```

`GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` turned telemetry on;
`ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` is the span content knob, set safe
**by the flag** — you wrote neither.

**Send a query and read the logs back.** Query the deployed agent, then read its
logs on the ReasoningEngine resource.

**Command:**

```bash
.venv/bin/python - "$ENGINE_ID" <<'PY'
import sys, vertexai
c = vertexai.Client(project="$GOOGLE_CLOUD_PROJECT", location="$REGION")
a = c.agent_engines.get(
    name=f"projects/$GOOGLE_CLOUD_PROJECT/locations/$REGION/reasoningEngines/{sys.argv[1]}"
)
for ev in a.stream_query(user_id="u1", message="What's the weather in London?"):
    pass
print("query sent")
PY

gcloud logging read \
  'resource.type="aiplatform.googleapis.com/ReasoningEngine"
   resource.labels.reasoning_engine_id="'"$ENGINE_ID"'"' \
  --project="$PROJECT_ID" \
  --limit=10 \
  --format='value(logName.basename(), textPayload)'
```

**Expected output** — the framework INFO lines, on the **stderr** log:

```console
reasoning_engine_stderr    ... - INFO - google_llm.py:255 - Sending out request, model: gemini-3.7-flash, backend: GoogleLLMVariant.VERTEX_AI, stream: False
reasoning_engine_stderr    ... - INFO - agent.py:54 - tool get_weather called for city='London'
reasoning_engine_stderr    ... - INFO - google_llm.py:327 - Response received from the model.
```

> [!IMPORTANT]
> **What Agent Runtime does NOT do, that Cloud Run did.** On Cloud Run (5.4) the
> same flag put `gen_ai.*` events in Cloud Logging. On Agent Runtime, with
> telemetry enabled and the env vars correctly set, **no `gen_ai.*` log names and
> no Cloud Trace spans surfaced in our testing** — only the framework's own
> `reasoning_engine_stderr` INFO lines (the ADK-native logging from Part 1,
> captured by the platform). Where the OTel telemetry lands on a native Agent
> Runtime deploy is an **open question** — see the Verification status in
> [Part 7](07-how-to-choose.md). What this section *does* verify is what each
> enablement route writes to the deployment, which the env lists below prove.

---

### 6.3 Deploy B: the `.env` route

Same script, `ENABLE_VIA_ENV=1`: it writes `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`
**and both content knobs** into the temporary `.env`, and deploys with **no**
`--otel_to_cloud`. This is the route where you must set the knobs yourself; the
script does it so the deploy is safe.

**Command:**

```bash
source env.sh
export ENGINE_ID_ENV=$(ENABLE_VIA_ENV=1 ./deploy/deploy_agent_engine.sh | sed -n 's/^ENGINE_ID=//p')
```

**Read this deployment's env list** (same SDK command as 6.2, with
`$ENGINE_ID_ENV`). It shows exactly the lines the `.env` carried — and, unlike
6.2, nothing the CLI added on its own:

**Expected output:**

```console
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_LOCATION=global
LOG_LEVEL=info
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT
```

Compare with 6.2. There, `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` was the
only content knob and the **CLI** added it. Here all three telemetry lines came
from `.env` — the script wrote them, including the event knob
`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT` that the flag
route never set. That is the `.env` route's whole lesson: the CLI adds nothing,
so every knob is yours to set.

The lesson: on the `.env` route the CLI adds no content knobs. If the script had
not written `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` itself, prompt text
would ride on the spans. On the flag route (6.2) the CLI sets that for you; here
it is on you.

---

### 6.4 What the platform changes

Reading the two deploys back shows what Agent Runtime does differently from a
local run or Cloud Run — stated as only what the read-backs actually showed:

| On a native Agent Runtime deploy | What we observed |
|---|---|
| **The enablement switch** | One env var, `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY`, on the deployment — not a flag reaching a server process. Both routes set it to `true` (env lists above). |
| **Who sets the content knobs** | The flag route also sets `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` for you; the `.env` route sets nothing, so you set both knobs yourself. Proven by the two env lists. |
| **The logs you get** | The framework INFO lines land on `aiplatform.googleapis.com/reasoning_engine_stderr` (stdout carries only access lines). Same ADK-native logging as Part 1, captured by the platform. |
| **The `gen_ai.*` OTel events** | Did **not** surface in Cloud Logging or Cloud Trace in our testing, unlike Cloud Run (5.4). Open question — see Part 7 Verification status. |

Do not extend this list past what you can see in your own project's console; the
platform's telemetry routing is the part this tutorial could not pin down.

---

If you scaffold with `agents-cli`, the generated project wires a
`setup_telemetry()` for you and gates a richer prompt-response logging tier on a
`LOGS_BUCKET_NAME` (exported to GCS and BigQuery). That is the same OTel machinery
from Part 5, pre-wired.

---

← Prev: [5. OpenTelemetry](05-otel.md) · [Tutorial index](../TUTORIAL.md) · Next: [How to choose & reference](07-how-to-choose.md) →

