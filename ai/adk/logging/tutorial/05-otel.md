# Part 5 · OpenTelemetry

*Stream 4 — the spans ADK already emits with nothing configured, and where they
go once you point them at Google Cloud.*

> [!NOTE]
> **Why you are here.** Parts 1-4 were all the `logging` module: streams 1, 2 and 3,
> text you read a line at a time or query a field at a time. Stream 4 is different
> machinery. ADK emits **OpenTelemetry** spans, GenAI log events, and metrics, and
> none of them print. They leave through an exporter. You want them because a span
> tree answers *where did the time go* and *what did each step actually receive*,
> which no flat log line can. The surprise this part opens with is that you do not
> configure anything to get them: `adk web` traces every turn already. What the
> flag in 5.2 adds is not tracing, it is **export**.

Part 5 starts from what is already running (5.0, 5.1), adds one flag to send it to
Google Cloud (5.2 onward), and only writes code in the one situation that needs it.

---

### 5.0 What stream 4 is

Streams 1-3 are Python `logging`: a record, a level, a handler, a line of text.
Stream 4 shares none of that. It is a separate SDK with its own three signals, all
produced by ADK itself with no extra packages and no instrumentation on your part:

| Signal | What ADK produces | Shape |
|---|---|---|
| **Traces** | one span per invocation, agent, model call and tool call | a nested tree with durations and attributes |
| **Log events** | `gen_ai.system.message`, `gen_ai.user.message`, `gen_ai.choice` | structured events, stamped with the current trace and span id |
| **Metrics** | `gen_ai.client.token.usage`, `gen_ai.execute_tool.duration`, and friends | counters and histograms |

The whole part turns on one question: **where does that go?** There are two
answers, and 5.1 and 5.2 are exactly those two.

```mermaid
flowchart LR
  subgraph proc["one agent process · stream 4"]
    sp["spans<br/>invocation · invoke_agent<br/>call_llm · generate_content<br/>execute_tool"]
    ev["GenAI log events<br/>gen_ai.user.message · gen_ai.choice"]
    mt["metrics<br/>gen_ai.client.token.usage"]
  end
  subgraph def["default · nothing configured · 5.1"]
    d1["in-process exporters<br/>ApiServerSpanExporter<br/>InMemoryExporter"]
    d2["the Trace tab and<br/>/dev/.../debug/trace<br/>gone on restart"]
  end
  subgraph cloud["--otel_to_cloud · 5.2 onward"]
    c1["telemetry.googleapis.com<br/>traces + metrics"]
    c2["Cloud Logging<br/>gen_ai.* log names"]
  end
  sp --> d1 --> d2
  sp --> c1
  mt --> c1
  ev --> c2
```

*Stream 4's two destinations. The spans are produced either way; the flag only decides whether anything leaves the process.*

**The five span names.** Learn these once and every trace in this part reads
itself. Each one is created by ADK itself, at a line you can go read: source
paths below are relative to the installed `google/adk/` package, so
`telemetry/_instrumentation.py` is
`.venv/lib/python3.13/site-packages/google/adk/telemetry/_instrumentation.py`.

| Span name | Opened once per | Source |
|---|---|---|
| `invocation` | turn (the root span) | `telemetry/_instrumentation.py:133` |
| `invoke_agent {name}` | agent that runs | `telemetry/_instrumentation.py:470-476` |
| `call_llm` | model round trip | `flows/llm_flows/base_llm_flow.py:1732` |
| `generate_content {model}` | GenAI SDK call, inside `call_llm` | `telemetry/tracing.py:1068`, `:1122` |
| `execute_tool {tool}` | tool call | `telemetry/_instrumentation.py:507-509` |

Two more names show up in situations this tutorial does not exercise:
`send_data` on a live/streaming connection (`flows/llm_flows/base_llm_flow.py:717`)
and `execute_tool (merged)` when the model requests several tools in parallel
(`flows/llm_flows/functions.py:526`, `:774`).

---

### 5.1 With nothing configured, `adk web` is already tracing

> [!NOTE]
> **Why you are here.** The usual first move with OpenTelemetry is to go find an
> exporter to install. Do not. Run the agent the way Part 1 ran it, with no flags,
> no `OTEL_*` variables and no code, then open the dev UI and read the spans back
> by eye. Knowing what you get for free is what makes the rest of this part a
> short list of deltas rather than a pile of configuration.

**Step 1 — Start the dev UI.** No flags of any kind.

**Command:**

```bash
adk web ./
```

**Step 2 — Open the browser UI and send one turn.** Go to `localhost:8000`,
pick **demo_agent** from the app dropdown, and either start a new session or
reuse an existing one. Type the same prompt Part 1 used:

```
What's the weather in London?
```

The reply streams back in the chat pane ending in
`The weather in London is currently 15°C and drizzling.` Nothing in the chat UI
announces that anything was traced — it wasn't printed, it was captured.

**Step 3 — Click the Trace tab.** Same session, same turn: switch from the chat
view to the **Trace** tab. It renders the identical span tree you'd get from the
dev server's own debug endpoint (`/dev/apps/{app}/debug/trace/session/{id}`),
because that endpoint is what the tab calls — same spans, same nesting, same
durations. The tree for this turn:

```console
invocation  (4281 ms)
  invoke_agent weather_agent  (4270 ms)
    call_llm  (2649 ms)
      generate_content gemini-3.7-flash  (2641 ms)
      execute_tool get_weather  (1 ms)
    call_llm  (1583 ms)
      generate_content gemini-3.7-flash  (1580 ms)
```

> [!IMPORTANT]
> **What it means.** This is the run you have watched all tutorial, in the one shape
> a log cannot give you. Three things to read off it:
>
> | Reading | Why it matters |
> |---|---|
> | Five of the 5.0 span names, all present | ADK instrumented the turn itself; you added nothing |
> | 2649 ms + 1583 ms of model time against a **1 ms** tool | the latency question is answered by the tree, not by a stopwatch you wrote |
> | `execute_tool get_weather` is a **child of the first `call_llm`**, not its sibling | the tool span opens inside the model call that requested it, so a slow tool shows up as time inside the round trip that asked for it |
>
> Part 1 showed this same turn as five flat INFO lines in which the two round trips
> were distinguishable only by reading top to bottom. Here the nesting and the
> durations are the data — and the Trace tab is where you'd click into any node to
> see this same shape on your own run.

**Step 4 — Click the `execute_tool get_weather` span.** The tree is the shape;
one span is the detail. Selecting the node opens a panel of that span's fields:

| Field | Value here | What it is |
|---|---|---|
| Name | `execute_tool get_weather` | the span title, the standard GenAI verb plus your function's name |
| Span ID / Parent ID | `6237947…` / `9487881…` | the Parent ID is the first `call_llm`: the tool span opens inside the model call that requested it |
| Trace ID | `1.2672905…` | shared by every span in this turn, the join key across them |
| Start / End Time | `12:12:36` → `12:12:36` | the 1 ms you read off the tree, to the wall clock |
| Events → Event ID | `061fbc54…` | ADK's own event id, the join key back to the `/run` response's event list |

The panel is the durations and identity of one span. It does not show the tool's
arguments or return value: that is **content**, and where it lives, on which
span, and the knob that turns it off, is 5.2's subject.

**The endpoint behind the tab, for scripting.** The Trace tab is a UI over
`/dev/apps/{app}/debug/trace/session/{id}`, and that endpoint is still there if
you want the tree as raw JSON instead of clicking through it — `otel/check_local.sh`
uses exactly this endpoint to assert the five span names and their counts without
a browser. There is also a narrower view at `/dev/apps/{app}/debug/trace/{event_id}`,
keyed by that `gcp.vertex.agent.event_id`. It returns one span's attributes rather
than a tree, and it only ever sees three kinds of span: the exporter behind it
keeps `call_llm`, `send_data`, and anything starting with `execute_tool`, and
drops the rest (`cli/api_server.py:467-471`). Use the session view — or the Trace
tab, which reads the session view — when you want the whole picture.

**Where those spans have been living.** Three facts explain the entire output
above, and each is one place in the installed source:

1. **A real tracer provider is always installed.** The CLI's `_setup_telemetry`
   has three branches: `--otel_to_cloud`, then any `OTEL_EXPORTER_OTLP_*_ENDPOINT`
   variable, and then a plain `TracerProvider` when neither applies
   (`cli/api_server.py:649-666`). You took the third branch, and it is a
   working provider, not a no-op stub. That is why spans exist at all.
2. **Its exporters write to process memory.** Whichever branch runs, the server
   hands it the same two: `ApiServerSpanExporter`, which stashes attributes in a
   dict keyed by event id (`cli/api_server.py:458`), and `InMemoryExporter`,
   which keeps whole spans keyed by session (`:483`). Both are passed in at the
   call site (`:1170-1178`).
3. **Nothing leaves the process.** No network exporter is registered on that third
   branch. The spans live in the server's RAM, they are visible only through the
   Trace tab and the two `/dev` endpoints behind it, and they are gone when you
   press Ctrl-C. Restart `adk web` and reopen the same session's Trace tab: the
   session still exists in `demo_agent/.adk/session.db`, and the spans do not.

That last point is the whole reason 5.2 exists. You are not switching tracing on;
it is on. You are giving the spans somewhere durable to go.

Everything in this section is checked by
[otel/check_local.sh](../otel/check_local.sh), which starts a plain `adk web`,
runs one turn over HTTP against the debug endpoint behind the Trace tab, asserts
the five span names and their counts, and exits non-zero if any is missing. It
needs the model, and nothing else: no flag, no `OTEL_*` variable, no cloud
project.

---

### 5.2 One flag: `adk web --otel_to_cloud`, read the events back from Cloud Logging

> [!NOTE]
> **Why you are here.** 5.1 ended with the spans in the server's RAM and nowhere
> else. This section adds one flag and no code, then reads one turn back from
> **Cloud Logging** — the `gen_ai.*` events. The same flag also sends spans to
> Cloud Trace and metrics to Cloud Monitoring, but this section looks at logs
> only. It also answers the question that decides whether the flag is safe in
> production: the events carry no message text by default, and one knob turns
> text on.

**Before you start, once.** Everything from here to 5.4 authenticates and routes
the same way, so this list is not repeated. Do all of it on the machine that
runs `adk web`.

| Need | Do | Why |
|---|---|---|
| Application Default Credentials | `gcloud auth application-default login` | The flag's branch starts with `google.auth.default()`, which returns both the credentials and the project (`cli/api_server.py:680-718`, the call at `:700`). No key file and no `GOOGLE_API_KEY` are involved. |
| The project | `source env.sh` in the shell that starts the server | `google.auth.default()` takes the project from `GOOGLE_CLOUD_PROJECT` in the shell when it is set, and from your gcloud configuration otherwise (`google/auth/_default.py:698-720`, same site-packages). It does **not** come from `demo_agent/.env`: that file has not been loaded yet when this runs (the `.env` callout later in this section shows why). |
| The Telemetry API | `gcloud services enable telemetry.googleapis.com` on the project | Spans and metrics leave through `https://telemetry.googleapis.com/v1/traces` and `/v1/metrics` (`telemetry/google_cloud.py:57-69`). The GenAI events take a different road, the Cloud Logging API (`:264-281`). |
| Roles on the identity ADC resolves to | the table below | Three permissions, one per signal. |

The [Telemetry API overview](https://docs.cloud.google.com/stackdriver/docs/reference/telemetry/overview)
names two roles: `roles/telemetry.writer` on the project, and
`roles/serviceusage.serviceUsageConsumer` on the quota project (the metrics
request captured in this session carried an `x-goog-user-project` header, so
the quota project matters even when it is the same project). `gcloud iam roles
describe` shows what the candidate roles actually carry:

| Role | Permissions it carries | Covers |
|---|---|---|
| `roles/telemetry.writer` | `telemetry.traces.write`, `monitoring.timeSeries.create`, `logging.logEntries.create` | all three signals |
| `roles/telemetry.tracesWriter` | `telemetry.traces.write` | spans only |
| `roles/telemetry.metricsWriter` | `monitoring.timeSeries.create` | metrics only |
| `roles/cloudtrace.agent` | `cloudtrace.traces.patch`, `telemetry.traces.write` | spans, via the older Cloud Trace role |
| `roles/logging.logWriter` | `logging.logEntries.create`, `logging.logEntries.route` | the `gen_ai.*` events |

This section was run as a project owner, so the minimal set was not exercised.
`roles/telemetry.writer` plus the quota-project role is the documented answer;
the table tells you which permission a `403` is complaining about.

Packages: `requirements.txt` already installs them. `google-adk[otel-gcp]`
(explained after the read-back), `opentelemetry-exporter-otlp-proto-http` for
spans and metrics, and `opentelemetry-exporter-gcp-logging` for the events. That
last import is unguarded (`telemetry/google_cloud.py:272`), so it is not optional
once the flag is on.

**Step 1 — Export one shell variable, then start the dev UI with the flag
(terminal 1).** Stop the 5.1 server if it is still running. This `export` must be
in the shell **before** `adk web` starts. It cannot go in `demo_agent/.env`: the
exporters that read it are built when the server object is constructed, before
`.env` is ever loaded.

**Command:**

```bash
source env.sh
export OTEL_RESOURCE_ATTRIBUTES="service.instance.id=laptop-1,cloud.region=us-central1"
adk web --otel_to_cloud ./
```

Startup looks exactly like 5.1. Nothing prints to say that three exporters were
installed, and the flag's own help text says only `Whether to write OTel data to
Google Cloud Observability services - Cloud Trace and Cloud Logging`. (If you
installed ADK without the `[otel-gcp]` extra, one WARNING line appears before
`Started server process`; it is covered at the end of this section.)

Set `OTEL_RESOURCE_ATTRIBUTES` because without it every metrics export fails. This
section does not read metrics, but the failed batches print an error to terminal 1
every five seconds, so set it now. `cloud.region` must be a real region, not the
model's region and not `global`. Spans and log events need none of this; only
metrics do. The variable is a laptop-only workaround: on Cloud Run and Agent
Runtime the resource detector supplies a region and instance from the metadata
server. Nothing here opts into the experimental semantic convention yet. Steps 1
and 2 run under the stable `gen_ai.*` events, and Step 3 introduces the opt-in.

> [!WARNING]
> **Without `OTEL_RESOURCE_ATTRIBUTES`, every metrics export fails, and the error
> does not say why.** This section was first run without that line. Spans and
> events exported fine, and the terminal filled with one of these every 5 seconds
> for as long as the server ran:
>
> ```console
> 2026-09-04 17:21:03,454 - ERROR - __init__.py:294 - Failed to export metrics batch code: 400, reason: Bad Request
> 2026-09-04 17:21:08,556 - ERROR - __init__.py:294 - Failed to export metrics batch code: 400, reason: Bad Request
> ```
>
> The OTLP exporter logs the status and the reason and throws the body away
> (`opentelemetry/exporter/otlp/proto/http/metric_exporter/__init__.py:294`).
> Captured with a wrapped session, the body says:
>
> ```console
> {"errors":[{"code":"INVALID_ARGUMENT","error_message":"prometheus_target resource type must have an instance specified","num_data_points":1,"example_resource_attributes":{"gcp.project_id":"jwd-gcp-demos"}}]}
> ```
>
> The Telemetry API stores OTLP metrics as `prometheus_target` time series. That
> monitored resource requires an `instance` and a real `location`, which the API
> derives from `service.instance.id` and `cloud.region`. Off Agent Engine,
> `get_gcp_resource` starts from `{gcp.project_id}` and merges two detectors
> (`telemetry/google_cloud.py:335-352`): the OTel one reads
> `OTEL_RESOURCE_ATTRIBUTES` and `OTEL_SERVICE_NAME`, the Google Cloud one reads
> the metadata server, which a laptop does not have. So the resource is the
> project id alone, exactly as the error's `example_resource_attributes` shows,
> and every batch is rejected. Narrowing it down one attribute at a time:
> `service.instance.id` alone gets `write for resource failed: Unrecognized region
> or location.`; adding `cloud.region=global` gets `location / region / zone label
> cannot be set to "global"`; `cloud.region=us-central1` gets `200`.

Send one turn in the UI. Open `http://localhost:8000`, pick `demo_agent`, and in
the chat box ask the London question the rest of the tutorial uses:

```
What's the weather in London?
```

The dev UI creates the session for you and shows the reply, ending in something
like `The weather in London is currently 15°C and drizzling.` (the wording varies
run to run). Terminal 1 shows the same five INFO lines as always. Nothing
announces the export; the exporters batch in the background and print nothing on
success. Leave the server running.

Now read the turn back in the console. Open **Logs Explorer**
(`console.cloud.google.com/logs`), and query for `logName:"gen_ai."`. You will
find eight entries for the one turn: under the stable semantic convention this
section is still running, each message is its own log — `gen_ai.system.message`,
`gen_ai.user.message` (one per item the model saw), and `gen_ai.choice` for each
reply — spread across the two `call_llm` spans of the turn (five under one span
id, three under the other). Expand a `gen_ai.choice` entry:

**Expected output** — content elided, with the event's own fields in `jsonPayload`:

```console
{
  "jsonPayload": {
    "index": 0,
    "finish_reason": "STOP",
    "content": "<elided>"
  },
  "resource": {
    "type": "generic_node",
    "labels": { "location": "us-central1", "project_id": "jwd-gcp-demos", "namespace": "", "node_id": "" }
  },
  "labels": {
    "gen_ai.system": "vertex_ai",
    "event.name": "gen_ai.choice"
  },
  "logName": "projects/jwd-gcp-demos/logs/gen_ai.choice",
  "trace": "projects/jwd-gcp-demos/traces/c5fdba983e103412f76dbdf0175a5eb7",
  "spanId": "55f834ee252474c1"
}
```

> [!IMPORTANT]
> **What you are looking at.** Under the stable convention the message payload lands
> in `jsonPayload`, and the event name is a `labels` field:
>
> | Field | Value here | What it is |
> |---|---|---|
> | `jsonPayload.content` | `<elided>` | `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` defaults to `NO_CONTENT` (`telemetry/context.py:93-104`), so the entry records that a reply happened and nothing it said. Step 2 turns this on |
> | `labels.event.name` | `gen_ai.choice` | which of the split events this is; every entry of the turn is one of `system.message` / `user.message` / `choice` |
> | `trace` / `spanId` | `…c5fdba98…` / `55f834ee…` | the OTel API stamps the current span's trace and span id on every log record it emits. Part 4 built this join by hand from `X-Cloud-Trace-Context`; here it is free. The `trace` is shared by all eight entries; the `spanId` is one of the two `call_llm` spans |
> | `resource.type` | `generic_node` | the monitored resource, derived from the `OTEL_RESOURCE_ATTRIBUTES` in Step 1 |

**Step 2 — Turn content on, and see where it lands.** The events above proved the
turn happened but not what was said. One environment variable changes that. Stop
the server in terminal 1 with Ctrl-C, export the knob in the same shell (the Step
1 export is still set), and restart.

**Command:**

```bash
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
adk web --otel_to_cloud ./
```

Back in the UI, create a **new** session and ask the same London question:

```
What's the weather in London?
```

Then in Logs Explorer, query `logName:"gen_ai."` again and expand the newest
entries. The same eight events, but `jsonPayload.content` now holds the real
messages. The `gen_ai.system.message` carries the prompt verbatim:

**Expected output** — `gen_ai.system.message`, content now present:

```console
{
  "jsonPayload": {
    "content": "You are a concise weather assistant. When the user asks about weather, call the get_weather tool and report its result in one sentence. If the tool returns an error, say you do not have data for that city.\n\nYou are an agent. Your internal name is \"weather_agent\". The description about you is \"Answers questions about the weather in a few known cities.\"."
  },
  "labels": { "gen_ai.system": "vertex_ai", "event.name": "gen_ai.system.message" },
  "logName": "projects/jwd-gcp-demos/logs/gen_ai.system.message",
  "trace": "projects/jwd-gcp-demos/traces/9d24673b9690da24f0e5c44ad263e2fe",
  "spanId": "feed5573604bf3a9"
}
```

The final `gen_ai.choice` carries the reply and the model's structured turn — the
`function_call` to `get_weather`, the tool's `function_response`, and the answer:

**Expected output** — `gen_ai.choice`, the model's reply:

```console
{
  "jsonPayload": {
    "content": {
      "role": "model",
      "parts": [{ "text": "The weather in London is currently 15°C and drizzling." }]
    },
    "finish_reason": "STOP",
    "index": 0
  },
  "labels": { "gen_ai.system": "vertex_ai", "event.name": "gen_ai.choice" },
  "logName": "projects/jwd-gcp-demos/logs/gen_ai.choice",
  "trace": "projects/jwd-gcp-demos/traces/9d24673b9690da24f0e5c44ad263e2fe",
  "spanId": "89d9503ddd1fe465"
}
```

> [!IMPORTANT]
> **What to note.** Every message the model saw and produced is now in
> `jsonPayload.content`, where Step 1 showed `<elided>`: the system prompt, the
> user's `What's the weather in London?`, the `get_weather` call and its response,
> and the final sentence. Keep content **off** in production unless you have a
> reviewed reason to log prompts and replies — all of it lands in Cloud Logging
> under your project's retention and access rules.

Now check whether the content also landed on the **trace**, not only the logs.
Open **Trace Explorer** (`console.cloud.google.com/traces`), find this turn, and
click a `call_llm` span. Look at its attributes for `gcp.vertex.agent.llm_request`
and `gcp.vertex.agent.llm_response`.

> [!IMPORTANT]
> **What to note.** If those two span attributes hold the prompt and the reply text,
> then `=true` turned content on in **both** streams, logs and spans — and Step 3
> shows the knob that governs the spans alone. If instead the attributes are already
> empty here, `=true` only ever reached the logs, and Step 3 has nothing to turn off.

**Step 3 — Turn content off on the spans alone.** `=true` in Step 2 put content in
the logs, and (as the trace check showed) on the spans too. A second knob governs
the spans independently of the log events. Stop the server, add the span knob to
the same shell (the event knob is still `true`), and restart.

**Command:**

```bash
export ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false
adk web --otel_to_cloud ./
```

Ask the London question in a new session once more:

```
What's the weather in London?
```

In Logs Explorer the `gen_ai.*` events still carry content (the event knob is still
`true`), but in Trace Explorer the `call_llm` span's `gcp.vertex.agent.llm_request`
/ `llm_response` attributes are now `{}` — content is off on the spans and on in the
logs, independently.

> [!IMPORTANT]
> **What to note.** The two content streams have separate knobs.
> `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` (Step 2) governs the
> **log events**; `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS` governs the **span
> attributes**. Turning one off does not touch the other, so a production setup can
> keep spans clean while still logging content, or the reverse.

**Step 4 — Switch to the experimental semantic convention.** Everything so far ran
under the stable convention, which emits one log per message. The Agent Runtime
docs page, and the rest of this tutorial, run under the **experimental** one, which
is shaped differently. Stop the server, add the opt-in, put the content knob back
to `NO_CONTENT` (this step isolates the convention change from the content change),
and restart.

**Command:**

```bash
export OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT
adk web --otel_to_cloud ./
```

Ask the London question in a new session:

```
What's the weather in London?
```

Then query `logName:"gen_ai."` in Logs Explorer once more. The entry set changes
shape: instead of the split `system.message` / `user.message` / `choice` logs, you
get **one** `gen_ai.client.inference.operation.details` entry per `call_llm` span,
two for the turn. Expand one and it looks like this:

**Expected output** — one consolidated event, content off, metadata in `labels`:

```console
{
  "resource": {
    "type": "generic_node",
    "labels": { "project_id": "jwd-gcp-demos", "location": "us-central1", "namespace": "", "node_id": "" }
  },
  "labels": {
    "event.name": "gen_ai.client.inference.operation.details",
    "gen_ai.agent.name": "weather_agent",
    "gen_ai.conversation.id": "dc14be27-393e-4126-a304-16860701713e",
    "gcp.vertex.agent.invocation_id": "e-c290004b-ae01-4baf-9561-26e51abf80fe",
    "gcp.vertex.agent.event_id": "e2a2cd65-b110-4092-a9d7-a8ce9a101927",
    "gen_ai.usage.input_tokens": "229",
    "gen_ai.usage.output_tokens": "15",
    "gen_ai.response.finish_reasons": "[\"stop\"]",
    "gen_ai.tool.definitions": "[{\"name\":\"get_weather\",\"description\":\"Return the current weather for a city.\\n\\nArgs:\\n  city: The city to look up, for example \\\"San Francisco\\\".\\n\\nReturns:\\n  A dict with a ``status`` and either a ``report`` or an ``error_message``.\",\"parameters\":null,\"type\":\"function\"}]"
  },
  "logName": "projects/jwd-gcp-demos/logs/gen_ai.client.inference.operation.details",
  "trace": "projects/jwd-gcp-demos/traces/3b80ad2b7b2b996092831043a1611f4d",
  "spanId": "849de272916dd81f"
}
```

The entry has **no `jsonPayload`** at all — everything is in `labels`, and none of
it is message content.

> [!IMPORTANT]
> **What you are looking at.** The experimental convention folds a whole model call
> into one entry, and puts the metadata in `labels` rather than `jsonPayload`:
>
> | Field | Value here | What it is |
> |---|---|---|
> | `event.name` | `gen_ai.client.inference.operation.details` | one consolidated inference event, not the per-message split of Steps 1-3 |
> | `gen_ai.usage.input_tokens` / `output_tokens` | `229` / `15` | token counts for this call, right in the entry |
> | `gen_ai.response.finish_reasons` | `["stop"]` | how the model stopped |
> | `gen_ai.tool.definitions` | the `get_weather` schema | the tools the model was offered — definitions, not calls |
> | `trace` / `spanId` | `…3b80ad2b…` / `849de272…` | the join key to the `call_llm` span, as before |
> | *(message content)* | **absent** | `NO_CONTENT` again: usage and shape, nothing said. No `jsonPayload.content`, no message text in `labels` |

**Step 5 — Turn content on under the experimental convention.** Same event knob as
Step 2, on the new event shape. Stop the server, flip content to `EVENT_ONLY`,
restart.

**Command:**

```bash
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=EVENT_ONLY
adk web --otel_to_cloud ./
```

Ask the London question in a new session:

```
What's the weather in London?
```

Then expand the newest `gen_ai.client.inference.operation.details` entry in Logs
Explorer. The same consolidated shape as Step 4, but three content labels are now
filled in — and they are still `labels`, not `jsonPayload`:

**Expected output** — the final model call, content now in `labels`:

```console
{
  "labels": {
    "event.name": "gen_ai.client.inference.operation.details",
    "gen_ai.agent.name": "weather_agent",
    "gen_ai.usage.input_tokens": "229",
    "gen_ai.usage.output_tokens": "15",
    "gen_ai.response.finish_reasons": "[\"stop\"]",
    "gen_ai.system_instructions": "[{\"content\":\"You are a concise weather assistant. ...\",\"type\":\"text\"}]",
    "gen_ai.input.messages": "[{\"role\":\"user\",\"parts\":[{\"content\":\"What's the weather in London?\\n\",\"type\":\"text\"}]},{\"role\":\"assistant\",\"parts\":[{\"arguments\":{\"city\":\"London\"},\"name\":\"get_weather\",\"id\":\"call_397575\",\"type\":\"tool_call\"}]},{\"role\":\"user\",\"parts\":[{\"response\":{\"status\":\"ok\",\"report\":\"The weather in London is 15C and drizzling.\"},\"id\":\"call_397575\",\"type\":\"tool_call_response\"}]}]",
    "gen_ai.output.messages": "[{\"role\":\"assistant\",\"parts\":[{\"content\":\"The weather in London is currently 15\\u00b0C and drizzling.\",\"type\":\"text\"}],\"finish_reason\":\"stop\"}]"
  },
  "logName": "projects/jwd-gcp-demos/logs/gen_ai.client.inference.operation.details",
  "trace": "projects/jwd-gcp-demos/traces/acacdad756293b70e0b9b8eef517d0ad",
  "spanId": "526c426af55360ea"
}
```

> [!IMPORTANT]
> **What to note.** `EVENT_ONLY` adds three content labels that Step 4's `NO_CONTENT`
> left off, and folds the whole conversation into them:
>
> | Label | Holds |
> |---|---|
> | `gen_ai.system_instructions` | the system prompt |
> | `gen_ai.input.messages` | everything the model saw this call — the question, the `get_weather` tool call, and the tool's response — as one JSON array |
> | `gen_ai.output.messages` | the model's reply, with its `finish_reason` |
>
> Two things carry forward. First, the content is in **`labels`**, as JSON strings —
> the experimental convention has no `jsonPayload` even with content on, unlike the
> stable per-message logs of Step 2. Second, the same production caution: leave
> content off unless you have a reviewed reason to log it. Both knobs are shell
> exports for this run only; they do not persist to later sections.

> [!WARNING]
> **Can `.env` turn any of this on?** No. Not the flag, and not the `OTEL_*`
> variables you exported across the steps above. The agent's `.env` is loaded when the
> agent itself is first loaded (`cli/utils/agent_loader.py:331-332`), which
> happens on the first request that needs it. The exporters were chosen, and the
> knobs read, when the server object was built, in `_setup_telemetry`
> (`cli/api_server.py:1173-1179`), before any request existed. The only branch
> that reads `.env` at startup belongs to the older `--trace_to_cloud` flag
> (`cli/fast_api.py:312-328`), which the source marks for removal. The server log
> shows the order; this excerpt is trimmed to the lines that matter:
>
> ```console
> INFO:     Application startup complete.
> INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
> INFO:     127.0.0.1:49686 - "GET /list-apps HTTP/1.1" 200 OK
> 2026-09-04 18:48:07,909 - INFO - api_server.py:1092 - New session created: s5-knob
> INFO:     127.0.0.1:49693 - "POST /apps/demo_agent/users/u1/sessions/s5-knob HTTP/1.1" 200 OK
> 2026-09-04 18:48:07,931 - INFO - envs.py:83 - Loaded .env file for demo_agent at /Users/jeff/Desktop/Dev/gcp-demos/ai/adk/logging/demo_agent/.env
> 2026-09-04 18:48:07,933 - INFO - agent_loader.py:188 - Found root_agent in demo_agent.agent
> ```
>
> Startup completed, requests were served, a session was created, and only then,
> on the first `/run`, was `.env` read. Anything that has to be decided before
> that point comes from the command line or the shell: the flag here, and the
> `OTEL_*` exports in the steps above. The exporter endpoint variables in 5.7 are
> the same story.

**The startup WARNING, and what `[otel-gcp]` adds.** With the flag on, ADK tries
to import Google's GenAI SDK instrumentor and activate it
(`cli/api_server.py:738-750`). Installed without the extra, startup logs one line
and carries on.

**Expected output** — at startup, only when the extra is missing:

```console
2026-09-04 17:20:58,660 - WARNING - api_server.py:747 - Unable to import GoogleGenAiSdkInstrumentor - some telemetry will be disabled. Make sure to install google-adk[otel-gcp]
```

`requirements.txt` installs `google-adk[otel-gcp]` (the instrumentor plus its
supporting packages), so you will not see this line; if you do,
`pip install "google-adk[otel-gcp]"` is the fix. The extra also supplies the
`opentelemetry-instrumentation-google-genai` instrumentor, which creates the
`generate_content` spans and the client token metrics you would see on the trace
tree and in Cloud Monitoring. On a laptop its `httpx` and gRPC companions stay
off; ADK activates them only under `GOOGLE_CLOUD_AGENT_ENGINE_ID`
(`cli/api_server.py:751-767`).

Everything you have read back so far came from the dev UI's server, through Cloud
Logging alone. 5.3 keeps the same flag on `adk api_server`, and reads the same
`gen_ai.*` events back with `curl` in and Cloud Logging out.

---

### 5.3 The same flag on `adk api_server`

> [!NOTE]
> **Why you are here.** 5.2 ran `adk web --otel_to_cloud` and read the turn back
> from Cloud Logging. `adk api_server` is the headless twin: no Trace tab, no
> `/dev` debug routes (5.1's WARNING already showed those 404), but the exact same
> telemetry. Both commands share one option group
> (`fast_api_common_options`) and build the server through the same
> `ApiServer.get_fast_api_app`, where `_setup_telemetry` runs
> (`cli/api_server.py:1173`). Put the flag on `api_server` and you take the
> identical branch 5.2 took. This section is curl in, Cloud Logging out.

**Step 1 — Export the three variables (terminal 1), before starting the server.**

**Command:**

```bash
source env.sh
export OTEL_RESOURCE_ATTRIBUTES="service.instance.id=laptop-1,cloud.region=us-central1"
export OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT
```

| Variable | Value | Why |
|---|---|---|
| `OTEL_RESOURCE_ATTRIBUTES` | `service.instance.id=laptop-1,cloud.region=us-central1` | Same reason as 5.2's WARNING: without a `service.instance.id` and a real `cloud.region`, every metrics batch to `telemetry.googleapis.com` gets rejected with a 400 the terminal never explains. |
| `OTEL_SEMCONV_STABILITY_OPT_IN` | `gen_ai_latest_experimental` | Matches 5.2 and the Agent Runtime docs page. |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | `NO_CONTENT` | This is already the default (5.2, Step 4), set here explicitly since 5.2 turned it on and this section keeps it off — the production value. |

**Step 2 — Start the API server (terminal 1).**

**Command:**

```bash
adk api_server --otel_to_cloud ./
```

**Step 3 — Send one turn (terminal 2).** The same session-create-then-`/run` pair as 1.3 and 5.1, on a fresh session.

**Command:**

```bash
source env.sh
START=$(date -u +%Y-%m-%dT%H:%M:%SZ)

curl -s -X POST localhost:8000/apps/demo_agent/users/u1/sessions/s5-api \
     -H 'content-type: application/json' -d '{}'

curl -s -X POST localhost:8000/run \
     -H 'content-type: application/json' \
     -d '{"app_name":"demo_agent","user_id":"u1","session_id":"s5-api",
          "new_message":{"role":"user","parts":[{"text":"What'\''s the weather in London?"}]}}'
```

```console
TODO(verify): adk api_server --otel_to_cloud ./, with the three exports from
Step 1 set, run against the curl /run block above (session s5-api, London
question). Expect the same event-list response shape as 5.1/5.2, ending in a
weather-report sentence, and the same five INFO lines in terminal 1. Capture
the actual response text here.
```

**Step 4 — Read the `gen_ai.*` events back from Cloud Logging.** Same query shape as 5.2 Step 4, filtered to this run's window.

**Command:**

```bash
gcloud logging read \
  'logName:"gen_ai." timestamp>="'"$START"'"' \
  --project="$PROJECT_ID" \
  --limit=8 \
  --format='table(logName.basename(),jsonPayload.content,trace,spanId,resource.type)' \
  --freshness=1h
```

```console
TODO(verify): gcloud logging read as above, immediately after the Step 3 /run
call against adk api_server --otel_to_cloud. Expect eight gen_ai.* entries
(gen_ai.system.message, gen_ai.user.message ×N, gen_ai.choice, split across the
two call_llm spans as in 5.2 Step 4), CONTENT column <elided> on every row
(OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT), a single
shared trace id across all rows split by two spanId values, and resource.type
generic_task (OTEL_RESOURCE_ATTRIBUTES set, per 5.2's WARNING). Capture the
real trace id, span ids, and row count here.
```

> [!IMPORTANT]
> **What it means.** `<elided>` content on every row confirms the `NO_CONTENT`
> export took: 5.2 turned content on with `EVENT_ONLY`, and 5.3 kept it off, the
> production value. The trace and span ids are the join key back to Cloud Trace:
> reading the span tree and the token metric for this run is the same path either
> command installs, curl or UI making no difference to what `_setup_telemetry`
> set up. Not shown here — this section stays on the logs.

Same flag, same code path, headless: `adk api_server --otel_to_cloud` puts the
turn in Cloud Logging with nothing but curl and three exports. 5.4 takes this
one step further and ships the same flag to Cloud Run with
`adk deploy cloud_run --otel_to_cloud`, where the process runs under a service
account instead of your ADC login.

---

*Sections 5.4 to 5.8 (Cloud Run in full, your own server, the content knobs
as reference, other OTLP backends, and how stream 4 relates to Parts 1 to 4)
are not yet rewritten. Until they are,
[examples/08_otel_cloud.py](../examples/08_otel_cloud.py) shows the two calls a
hand-written server makes to install the same exporters the CLI installs, and
its docstring explains its modes.*

---

← Prev: [4. Structured logging](04-production.md) · [Tutorial index](../TUTORIAL.md) · Next: [6. Agent Runtime](06-agent-runtime.md) →
