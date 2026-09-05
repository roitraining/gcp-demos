[→ 6.1 · One switch, two ways to set it](6.1-one-switch.md)<br>
[← 5.8 · How this relates to Parts 1-4](../part-5/5.8-relates-to-parts-1-4.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

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

## In this part

| Section | What it covers |
|---|---|
| [6.1 · One switch, two ways](6.1-one-switch.md) | The single env var and the two non-equivalent ways to set it. |
| [6.2 · Deploy A: the flag](6.2-deploy-flag.md) | Deploy with `--otel_to_cloud`; read the env list back. |
| [6.3 · Deploy B: the `.env` route](6.3-deploy-env.md) | Enable via `.env`; you set the content knobs yourself. |
| [6.4 · What the platform changes](6.4-platform-changes.md) | What the two read-backs actually showed, and no further. |

---

[→ 6.1 · One switch, two ways to set it](6.1-one-switch.md)<br>
[← 5.8 · How this relates to Parts 1-4](../part-5/5.8-relates-to-parts-1-4.md)<br>
[Tutorial index](../../TUTORIAL.md)
