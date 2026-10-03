[← 5.8 · How this relates to Parts 1-4](../part-5/5.8-relates-to-parts-1-4.md)<br>
[→ 6.1 · One switch, two ways to set it](6.1-one-switch.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 6 · Agent Runtime

*The telemetry layer on Agent Runtime, and what plugin code carries over.*

> [!NOTE]
> **Why you are here.** 1.6 and 1.7 covered logging on Agent Runtime: a native
> deploy takes your format, a custom container keeps it. This part adds the
> telemetry layer (stream 4) on top.

Agent Runtime here means a native deploy with `adk deploy agent_engine`, not
your own container. You do not write the server; the CLI generates one that
runs `adk api_server`. Logs land on the `aiplatform.googleapis.com/ReasoningEngine`
resource, with the agent and framework lines on `reasoning_engine_stderr` and
only the access lines on `reasoning_engine_stdout`. Passing `--otel_to_cloud`,
or setting `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` in `.env`, puts
`--otel_to_cloud` on that server's start command and sets the env var on the
deployment. Your Part 4 structured plugin should work here unchanged, without
the trace-header parsing; that is not run in this tutorial.

## In this part

| Section | What it covers |
|---|---|
| [6.1 · One switch, two ways to set it](6.1-one-switch.md) | The single env var and the two non-equivalent ways to set it. |
| [6.2 · Deploy A: the flag](6.2-deploy-flag.md) | Deploy with `--otel_to_cloud`; read the env list back. |
| [6.3 · Deploy B: the `.env` route](6.3-deploy-env.md) | Enable via `.env`; you set the content knobs yourself. |
| [6.4 · What the platform changes](6.4-platform-changes.md) | What the two read-backs showed, and no further. |

---

[← 5.8 · How this relates to Parts 1-4](../part-5/5.8-relates-to-parts-1-4.md)<br>
[→ 6.1 · One switch, two ways to set it](6.1-one-switch.md)<br>
[Tutorial index](../../TUTORIAL.md)
