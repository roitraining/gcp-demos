[← 5.8 · How this relates to Parts 1-4](../part-5/5.8-relates-to-parts-1-4.md)<br>
[→ 6.1 · One switch, two ways to set it](6.1-one-switch.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 6 · Agent Runtime

*The telemetry layer on Vertex AI Agent Engine, and what plugin code carries over.*

> [!NOTE]
> **Why you are here.** 1.6 covered logging on Agent Engine: native deploys give
> the platform your format, BYOC keeps it. This part adds the telemetry layer
> (stream 4) on top, and states the operational facts once.

On a native deploy you do not run uvicorn or write JSON lines; the platform
captures the container's output. Logs land on the
`aiplatform.googleapis.com/ReasoningEngine` resource, with the agent and
framework lines on `reasoning_engine_stderr` and only the access lines on
`reasoning_engine_stdout`. Read by resource type to catch both.

Your Part 4 structured plugin works here unchanged: its records are captured
with the same structured fields you get on Cloud Run. Drop the trace-header
parsing, because the platform handles request correlation. Write the plugin
once, use it on a local server, Cloud Run, and Agent Engine.

There is no `--otel_to_cloud` flag reaching a server process here. Telemetry is
governed by one env var on the deployment, and every tool is a different way to
write it.

## In this part

| Section | What it covers |
|---|---|
| [6.1 · One switch, two ways](6.1-one-switch.md) | The single env var and the two non-equivalent ways to set it. |
| [6.2 · Deploy A: the flag](6.2-deploy-flag.md) | Deploy with `--otel_to_cloud`; read the env list back. |
| [6.3 · Deploy B: the `.env` route](6.3-deploy-env.md) | Enable via `.env`; you set the content knobs yourself. |
| [6.4 · What the platform changes](6.4-platform-changes.md) | What the two read-backs showed, and no further. |

---

[← 5.8 · How this relates to Parts 1-4](../part-5/5.8-relates-to-parts-1-4.md)<br>
[→ 6.1 · One switch, two ways to set it](6.1-one-switch.md)<br>
[Tutorial index](../../TUTORIAL.md)
