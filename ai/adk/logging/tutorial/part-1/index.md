[→ 1.1 · The basic test harness](1.1-test-harness.md)<br>
[← Setup](../00-setup.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 1 · The log level

*What `DEBUG`, `INFO`, `WARNING`, and `ERROR` each reveal — on a script,
`adk web`, and `adk api_server`.*

> [!NOTE]
> **Why you are here.** The log level is the first and bluntest dial. Before adding
> any plugin or custom formatter, you need to know exactly what `DEBUG`, `INFO`,
> `WARNING`, and `ERROR` each reveal, so you can pick the right one instead of
> drowning in output or flying blind. This part is a guided tour of that dial.


Part 1 runs the same one question, *"What's the weather in Tokyo?"*, three ways:
first through a plain script where you control the level directly (1.1), then
through each of the two servers ADK ships (1.2, 1.3).

## In this part

| Section | What it covers |
|---|---|
| [1.1 · The basic test harness](1.1-test-harness.md) | The script that runs one question at any level |
| [1.2 · The same dial on `adk web`](1.2-adk-web.md) | The `--log_level` flag on the dev UI |
| [1.3 · The same dial on `adk api_server`](1.3-adk-api-server.md) | Same dial over HTTP, plus the access log |
| [1.4 · The same script on Cloud Run](1.4-cloud-run.md) | What Cloud Logging does to an unmodified run |
| [1.5 · The same logging behind a real HTTP server](1.5-http-server.md) | All four streams land together on a service |
| [1.6 · The same agent on Agent Runtime](1.6-agent-runtime.md) | Native vs BYOC, and who owns the format |

---

[→ 1.1 · The basic test harness](1.1-test-harness.md)<br>
[← Setup](../00-setup.md)<br>
[Tutorial index](../../TUTORIAL.md)
