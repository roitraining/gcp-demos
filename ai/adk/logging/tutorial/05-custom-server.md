# Part 5 · A custom server

*A hand-written FastAPI service where one `dictConfig` owns all four streams.*

> [!NOTE]
> **Why you are here.** You are not using `adk web`, `adk api_server`, or ADK's
> `get_fast_api_app` helper. You have a hand-written FastAPI service (a common
> situation once you need custom routes, auth, or streaming), and you want to
> configure all four streams in one place. Note that `get_fast_api_app` has no
> `log_level` parameter either, so owning the logging config is the norm for any
> custom server, not an edge case.

[examples/06_custom_server.py](../examples/06_custom_server.py) is a complete,
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

**👉 Do this.**

```bash
.venv/bin/python examples/06_custom_server.py
# in another terminal:
curl -s -X POST localhost:8080/chat -H 'content-type: application/json' \
     -d '{"message":"weather in Tokyo?"}'
```

**Expected output** — the structured telemetry from your Part 4 plugin on the server's
stdout, followed by the HTTP response to the client:

```console
{"severity": "INFO", "message": "tool_start", "tool": "get_weather", "tool_args": {"city": "Tokyo"}}
{"severity": "INFO", "message": "tool_end", "tool": "get_weather", "latency_ms": 0.6, "status": "ok"}
{"response": "The weather in Tokyo is currently 27°C and humid."}
```

> [!IMPORTANT]
> **What it means.** One process, all four streams under your control in one config
> block, and the same structured events you designed in Part 4 now flowing out of a
> real HTTP server. This server is what Part 6 containerizes and ships.

---

← Prev: [4. Production logging](04-production.md) · [Tutorial index](../TUTORIAL.md) · Next: [6. Cloud Run](06-cloud-run.md) →

