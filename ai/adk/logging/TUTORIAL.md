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

```mermaid
flowchart LR
  subgraph proc["one agent process"]
    s1["1 · your code<br/>logging.getLogger(module name)"]
    s2["2 · ADK framework<br/>google_adk.*"]
    s3["3 · web server<br/>uvicorn.access"]
    s4["4 · OpenTelemetry<br/>spans + GenAI events"]
  end
  subgraph cfg["configured by"]
    c1["your logging config"]
    c2["getLogger('google_adk')<br/>or --log_level"]
    c3["uvicorn's own log_config"]
    c4["an exporter you install"]
  end
  subgraph dst["lands in"]
    d1["stdout / stderr<br/>→ Cloud Logging"]
    d2["Cloud Logging (gen_ai.*)<br/>+ Cloud Trace, or any OTLP collector"]
  end
  s1 --> c1 --> d1
  s2 --> c2 --> d1
  s3 -.-> c3 -.-> d1
  s4 --> c4 --> d2
```

*The four log streams, what configures each, and where they land.*

> Verified against **google-adk 2.8.0** on Python 3.13, serving Gemini 3.7 Flash
> through Vertex AI. Every command and every output block below is from a real
> run. Version-sensitive details are called out inline.

## Contents

The tutorial is split into short pages — one per part, and one per numbered
subtask under it. Read them in order (each page has a **Next →** link), or jump
to the one you need. Start with **Setup**, then work down.

**[0. Setup](tutorial/00-setup.md)** — do this once: environment, model, shell
variables, and the shared demo agent.

| Part | What it covers |
|---|---|
| [1. Log levels](tutorial/part-1/index.md) | The `DEBUG`/`INFO`/`WARNING`/`ERROR` dial on a script, `adk web`, `adk api_server`, Cloud Run, a real HTTP server, and Agent Runtime (1.1–1.6). |
| [2. Access logs](tutorial/part-2/index.md) | Why `--log_level` never silences uvicorn's access log, and how to filter it. |
| [3. Plugins](tutorial/part-3/index.md) | `LoggingPlugin` and `DebugLoggingPlugin` for readable step narration, local and on Cloud Run (3.1–3.5). |
| [4. Structured logging](tutorial/part-4/index.md) | A JSON `BasePlugin`, a custom server that owns all four streams, and that server on Cloud Run with explicit `severity` and a trace field that groups a request (4.1–4.4). |
| [5. OpenTelemetry](tutorial/part-5/index.md) | Stream 4: GenAI `gen_ai.*` events read back from Cloud Logging (locally, `adk api_server`, Cloud Run, your own server, other OTLP backends), and the content-capture privacy knob (5.0–5.8). |
| [6. Agent Runtime](tutorial/part-6/index.md) | The telemetry layer on Vertex AI Agent Engine, and what plugin code carries over (6.1–6.4). |
| [How to choose & reference](tutorial/how-to-choose.md) | The decision table, best-practice summary, verification status, and references. |

Ready? **[Start with Setup →](tutorial/00-setup.md)**
