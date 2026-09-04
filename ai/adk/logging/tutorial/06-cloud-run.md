# Part 6 · Cloud Run

*First-class logs: an explicit `severity` and a trace field that groups a request.*

> [!NOTE]
> **Why you are here.** In 1.5 you deployed a server to Cloud Run and got its logs
> into Cloud Logging for free, but as raw text with the wrong severity. Now you fix
> that: you want the logs to be first-class, correct severity, and grouped by
> request. Cloud Run's contract makes the ingestion part free, **anything a
> container writes to stdout/stderr is ingested into Cloud Logging automatically**,
> no sink to install. Your only job is to make each line a good JSON object. Two
> Cloud Run facts decide how.

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

[examples/07_cloudrun_json.py](../examples/07_cloudrun_json.py) does both. The clever
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

**👉 Do this**, passing the trace header the way Cloud Run would:

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

> [!TIP]
> **What it means.** That third line is a framework log you did not write, and it
> still carries the trace, because the `ContextVar` threads it through everything
> that runs during the request. In the Logs Explorer, clicking that trace shows all
> three lines grouped as one request, so you can read a single request's whole
> lifecycle across all four streams without hunting for the lines that belong to it.

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

Same two-step flow as [1.3](01a-log-levels-local.md#13-the-same-dial-on-adk-api_server), pointed at the
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

> [!TIP]
> **What it means.** The five-line lifecycle trail from 1.1.1 is intact, unchanged
> by deployment. What is new is a *third* line format: `POST 200 https://...` is
> Cloud Run's own request log, which exists alongside uvicorn's `INFO:` access line
> for the very same request. Stream 3 now has two writers, and neither is the
> `--log_level` flag's business.

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

---

← Prev: [5. Custom server](05-custom-server.md) · [Tutorial index](../TUTORIAL.md) · Next: [7. OpenTelemetry](07-otel.md) →

