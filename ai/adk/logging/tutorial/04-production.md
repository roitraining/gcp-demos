# Part 4 · Production logging

*A `BasePlugin` that emits queryable JSON `logging` records — plus callback vs.
plugin.*

> [!NOTE]
> **Why you are here.** You want the visibility of Part 3, but for a running
> service you can query, alert on, and correlate. That rules out `LoggingPlugin`
> (it prints) and DEBUG (it is unstructured text). The answer is to write a small
> plugin whose callbacks emit **real `logging` records** with structured fields.
> Because they go through the `logging` module, your handlers and formatters apply,
> so the *same plugin* prints readable text on your laptop and clean JSON in the
> cloud (Part 6). Write it once, reuse it everywhere you deploy.

A plugin's callbacks are the hook points. From
[examples/05_structured_plugin.py](../examples/05_structured_plugin.py), the
"after model" hook records latency and token usage:

```python
class StructuredTelemetryPlugin(BasePlugin):
    async def after_model_callback(self, *, callback_context, llm_response):
        usage = getattr(llm_response, "usage_metadata", None)
        telemetry_log.info("llm_response", extra={
            "event": "llm_response",
            "agent": callback_context.agent_name,
            "latency_ms": ...,                       # measured in the plugin
            "input_tokens": getattr(usage, "prompt_token_count", None),
            "output_tokens": getattr(usage, "candidates_token_count", None),
        })
        return None   # returning None means "proceed normally"
```

**👉 Do this.** The example attaches a JSON formatter to the telemetry logger and
asks *"What's the weather in New York?"*:

```bash
.venv/bin/python examples/05_structured_plugin.py
```

**You will see** one structured line per event:

```console
{"severity": "INFO", "message": "llm_response", "agent": "weather_agent", "latency_ms": 1617.0, "input_tokens": 141, "output_tokens": 6}
{"severity": "INFO", "message": "tool_start", "tool": "get_weather", "tool_args": {"city": "New York"}}
{"severity": "INFO", "message": "tool_end", "tool": "get_weather", "latency_ms": 0.2, "status": "ok"}
```

> [!TIP]
> **What it means.** Every line is now a machine-readable event, not prose. That is
> the prerequisite for querying: the fields you see here (`latency_ms`, `status`,
> `input_tokens`) become keys you can filter, aggregate, and alert on the moment
> these lines reach a log store. Nothing here is terminal-specific either, so the
> same script proves the point in the cloud.

**👉 Do this on Cloud Run.** Example 05 runs once and exits, so it is a Cloud Run
Job, exactly like the plugin scripts in 3.2 and 3.4, and the same deploy helper
takes this script as its argument:

```bash
export PROJECT_ID=your-project REGION=us-central1
SCRIPT=examples/05_structured_plugin.py ./deploy/deploy_plugin_job.sh
```

Cloud Run ingests the container's stdout automatically, and because each line is
JSON, Cloud Logging parses it into a `jsonPayload` object with your fields as keys.
The claim above is now a real query, filtering to one event type and reading
latency as a number:

```bash
gcloud logging read \
  'resource.type="cloud_run_job" jsonPayload.event="tool_end"' \
  --project="$PROJECT_ID" --freshness=15m \
  --format='table(jsonPayload.tool, jsonPayload.latency_ms, jsonPayload.status)'
```

**You will see** the structured fields returned as query columns, not text you
have to parse:

```console
TOOL         LATENCY_MS  STATUS
get_weather  0.5         ok
```

> [!TIP]
> **What it means.** No formatter change was needed: the JSON you saw on your laptop
> is the JSON Cloud Logging indexed. `jsonPayload.status="error"` is now an alerting
> condition and `jsonPayload.latency_ms` is a metric you can chart, both because the
> plugin emitted structured fields instead of prose, and `severity` rode along in
> the JSON, so Cloud Logging shows these as `INFO` rather than guessing. Part 6
> extends that to a long-running Service, putting the same correct severity *and* a
> shared trace id on **every** stream, including the framework and access logs your
> plugin never touches, so all of one request's lines group together.

Tear down the job when you are done:

```bash
gcloud run jobs delete adk-structured-job --project="$PROJECT_ID" --region="$REGION" --quiet
```

One detail this example teaches by doing:

- **Reserved field names.** Keys in `extra=` must not collide with built-in
  `LogRecord` attributes (`args`, `name`, `message`, `module`). The example uses
  `tool_args`, not `args`, precisely because `args` collides and raises a
  `KeyError` inside the log call. (This one bites everyone once.)

### 4.1 Callback or plugin?

> [!NOTE]
> **Why you are here.** The plugin above is one of two ways to emit your own
> records; the other is a per-agent callback, and you have probably seen that style
> elsewhere. Before choosing between them, be clear on what this logging is for. It
> does not replace ADK's built-in logging. It sits alongside it, because the two
> answer different questions.

To operate the agent you have to be able to answer questions like:

1. Is the model call failing or being retried?
2. Which tool ran, with which arguments, and did it succeed?
3. How many tokens did this turn cost, and what is a session costing?

Set a level on `google_adk` and the framework answers the first on its own:
requests sent, responses received, retries, and errors, for free. It does not
answer the second or third in any form you can query. At DEBUG it will dump the
tool call inside a wall of JSON you cannot filter or aggregate. Questions 2 and 3
are yours to collect as structured fields, and collecting them is the
callback-or-plugin job. So the rule is **in addition to the framework logger, not
instead of it.**

**The per-agent callback.** The same hook points exist on a single agent. Instead
of a plugin class, you attach a function:

```python
import logging

telemetry = logging.getLogger("agent.telemetry")   # your namespace, not google_adk

def log_tool(tool, args, tool_context):
    telemetry.info("tool_call", extra={
        "event": "tool_call",
        "tool": tool.name,
        "tool_args": args,
        "agent": tool_context.agent_name,
    })
    return None   # return a value instead to block or replace the call

root_agent = Agent(..., before_tool_callback=log_tool)
```

`getLogger("agent.telemetry")` returns a logger under a name you choose; the name
is arbitrary and unrelated to ADK. It matters for two reasons: you can set its
level and attach handlers by that same name in your logging config, and the name
rides on every record, so in Cloud Logging you can filter to `agent.telemetry`
and see your events without the framework's. Keeping it out of the `google_adk`
tree is what lets you control the two independently.

**Which to use.** The callback and the plugin run the same hooks; they differ in
scope.

| Use a plugin when... | Use a per-agent callback when... |
|---|---|
| you want uniform telemetry across every agent and tool | the logic belongs to one agent only |
| the logging carries state (a timer for latency) or config | you are prototyping and want the fewest lines |
| you want one field schema for downstream BigQuery or Looker analysis | you need to block or rewrite a step for that one agent |

A plugin registers once on the `App` and fires everywhere, which is why it is the
right default for production telemetry: one place, one schema, every agent. A
per-agent callback is siloed by design; with several agents the same logging
drifts across them and you cannot see the whole app at once. Reach for it when
the logic is genuinely local, or when you want a hook to **short-circuit**:
returning a value from a `before_*` callback stops or replaces the step, which
turns the same hook into a guardrail. Note that both callbacks and plugins run in
the request thread, so keep the work cheap and let the logging handler do the
shipping.

**The takeaway.** Set a level on ADK's logger to answer framework questions, add
a plugin (or, for one agent, a callback) to answer the tool and cost questions
ADK cannot, and route both through one logging config so every agent produces the
same queryable record.

---

← Prev: [3. Plugins](03-plugins.md) · [Tutorial index](../TUTORIAL.md) · Next: [5. Custom server](05-custom-server.md) →

