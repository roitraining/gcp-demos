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
- **Traces** appear in Cloud Trace automatically. Adding `--otel_to_cloud` exports
  logs and metrics too; under the hood the flag sets
  `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` on the deployed agent.
- Logs land on the `aiplatform.googleapis.com/ReasoningEngine` monitored
  resource. Note the stream: the agent and framework lines are on
  `aiplatform.googleapis.com/reasoning_engine_**stderr**`, not stdout, which
  carries only the web server's access lines (this trips people up, as 1.6
  showed). Read by resource type to catch both.

**Command:**

```bash
export PROJECT_ID=your-project
export REGION=us-central1
./deploy/deploy_agent_engine.sh
gcloud logging read \
  'resource.type="aiplatform.googleapis.com/ReasoningEngine"
   resource.labels.reasoning_engine_id="ENGINE_ID"' \
  --project="$PROJECT_ID" \
  --limit=20 \
  --format='table(severity,textPayload)'
```

**The reuse that matters.** Your Part 4 structured plugin still works here
unchanged: its records go to stdout and are captured, so you get the same
structured fields on Agent Engine that you get on Cloud Run. The one thing you
drop is the trace-header parsing from Part 4, because the platform handles request
correlation for you. Write the plugin once, use it in three places (local server,
Cloud Run, Agent Engine).

If you scaffold with `agents-cli`, the generated project wires a
`setup_telemetry()` for you and gates a richer prompt-response logging tier on a
`LOGS_BUCKET_NAME` (exported to GCS and BigQuery). That is the same OTel machinery
from Part 5, pre-wired.

---

← Prev: [5. OpenTelemetry](05-otel.md) · [Tutorial index](../TUTORIAL.md) · Next: [How to choose & reference](07-how-to-choose.md) →

