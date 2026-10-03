[← Setup](../00-setup.md)<br>
[→ 1.1 · The basic test harness](1.1-test-harness.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 1 · The log level

*What `DEBUG`, `INFO`, and `WARNING` each reveal, on a script, `adk web`,
`adk api_server`, Cloud Run, and Agent Runtime.*

> [!NOTE]
> **Why you are here.** The log level is the first and bluntest dial. This part
> shows what each level reveals, so you can pick a level that shows what you
> need without burying you in output.

Part 1 asks the same question, *"What's the weather in Tokyo?"*, through a plain
script (1.1), the two servers ADK ships (1.2, 1.3), and then the two places you
deploy (1.4 to 1.7).

## In this part

| Section | What it covers |
|---|---|
| [1.1 · The basic test harness](1.1-test-harness.md) | The script that runs one question at any level |
| [1.2 · The same dial on `adk web`](1.2-adk-web.md) | The `--log_level` flag on the dev UI |
| [1.3 · The same dial on `adk api_server`](1.3-adk-api-server.md) | Same dial over HTTP, plus the access log |
| [1.4 · The same script on Cloud Run](1.4-cloud-run.md) | What Cloud Logging does to an unmodified run |
| [1.5 · The same logging behind a real HTTP server](1.5-http-server.md) | Streams 1–3 land together on a service |
| [1.6 · The same agent on Agent Runtime](1.6-agent-runtime.md) | A native deploy, where the platform owns the format |
| [1.7 · The same agent in your own container on Agent Runtime](1.7-agent-runtime-byoc.md) | A custom container, where you own the format again |

---

[← Setup](../00-setup.md)<br>
[→ 1.1 · The basic test harness](1.1-test-harness.md)<br>
[Tutorial index](../../TUTORIAL.md)
