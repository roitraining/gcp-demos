# Part 3 · Plugins

*A clean, human-readable narration of the agent's steps —
`LoggingPlugin` and `DebugLoggingPlugin`, locally and on Cloud Run.*

> [!NOTE]
> **Why you are here.** INFO is too terse to debug a tool-calling problem (it tells
> you a request happened, not what the tool was called with), and DEBUG dumps the
> full model conversation as raw JSON. In development you often want the middle
> ground: a clean, human-readable narration of the agentic steps, which tool ran,
> with which arguments, what it returned, how many tokens it cost, without writing
> that yourself. ADK ships two plugins for exactly this. This part uses them
> locally first, then deploys each one to Cloud Run so you can see what a plugin
> sends to Cloud Logging, and closes with when to reach for a plugin at all.

---

### 3.1 LoggingPlugin: one line to wire up

A plugin attaches to the `App`. That is the whole setup, shown in
[examples/03_logging_plugin.py](../examples/03_logging_plugin.py):

```python
from google.adk.apps.app import App
from google.adk.plugins import LoggingPlugin

app = App(name="demo", root_agent=root_agent, plugins=[LoggingPlugin()])
```

The plugin's own docstring is blunt about its scope: it "is not a replacement of
existing logging in ADK," but rather "helps terminal based debugging" and
"serves as a simple demo for everyone to leverage when developing new plugins."
Read this section as much for how to write a plugin as for what this one prints.
The two deployed sections that follow (3.2, 3.4) are optional. We ran these
plugins on Cloud Run to satisfy a fair question, what would the cloud even do
with them, and the answer is instructive. But the takeaway is that you would not
actually ship either one; skip ahead to Part 4 if you only want the production
path.

**How the one line works.** A plugin is a set of lifecycle hooks. `BasePlugin`
declares fourteen async callbacks, `on_user_message_callback`,
`before_run_callback`, `before/after_agent_callback`,
`before/after_model_callback`, `before/after_tool_callback`, `on_event_callback`,
`after_run_callback`, three error hooks, and `close`, and every one returns
`None` by default. A plugin subclass overrides only the hooks it cares about.
`App(plugins=[...])` hands the list to a `PluginManager`, and at each point in a
run the runner calls the matching hook on every plugin, in registration order,
before any per-agent callback. The manager uses an early-exit rule:

> if any plugin
> callback returns a non-`None` value, the execution of subsequent plugins for
> that specific event is halted, and the returned value is propagated up the
> call stack.

`LoggingPlugin` returns `None` from every hook, so it never short-circuits
anything. It is a pure observer that prints and gets out of the way.

**What "no arguments" configures.** `LoggingPlugin()` takes only an optional
`name`; nothing else is configurable:

```python
def __init__(self, name: str = "logging_plugin"):
    super().__init__(name)
```

Everything about how it writes is fixed in the source:

| Setting | Value | Where |
|---|---|---|
| Line prefix | `[logging_plugin]`, the `name` | `_log` |
| Sink | `print()` to stdout, wrapped in grey ANSI codes | `_log` |
| Level, handler, formatter | none; the `logging` module is never touched | whole file |
| Text and system-instruction length | truncated at 200 characters | `_format_content` |
| Tool arguments and results length | truncated at 300 characters | `_format_args` |

The sink is the whole story, and it is four lines:

```python
def _log(self, message: str) -> None:
    # ANSI color codes: \033[90m for grey, \033[0m to reset
    formatted_message: str = f"\033[90m[{self.name}] {message}\033[0m"
    print(formatted_message)
```

Each hook just formats a few fields and calls `_log`. For example the
`TOOL STARTING` block you will see below is produced by `before_tool_callback`:

```python
async def before_tool_callback(self, *, tool, tool_args, tool_context):
    self._log(f"🔧 TOOL STARTING")
    self._log(f"   Tool Name: {tool.name}")
    self._log(f"   Agent: {tool_context.agent_name}")
    self._log(f"   Function Call ID: {tool_context.function_call_id}")
    self._log(f"   Arguments: {self._format_args(tool_args)}")
    return None
```

Because everything goes through `print()`, neither `--log_level` nor a
`dictConfig` can reach this output. That is the trait that decides where you use
it, called out at the end of this section.

**👉 Do this.**

```bash
.venv/bin/python examples/03_logging_plugin.py
```

The example asks *"What's the weather in London?"*

**Expected output** — the whole invocation narrated, one hook at a time (lightly
trimmed, repeated field lines removed):

<details>
<summary><b>Output</b> — full agentic-loop narration (29 lines)</summary>

```console
[logging_plugin] 🚀 USER MESSAGE RECEIVED
[logging_plugin]    User Content: text: 'What's the weather in London?'
[logging_plugin] 🏃 INVOCATION STARTING
[logging_plugin] 🤖 AGENT STARTING
[logging_plugin]    Agent Name: weather_agent
[logging_plugin] 🧠 LLM REQUEST
[logging_plugin]    Model: gemini-3.7-flash
[logging_plugin]    System Instruction: 'You are a concise weather assistant. ...'
[logging_plugin]    Available Tools: ['get_weather']
[logging_plugin] 🧠 LLM RESPONSE
[logging_plugin]    Content: function_call: get_weather
[logging_plugin]    Token Usage - Input: 167, Output: 16
[logging_plugin] 📢 EVENT YIELDED
[logging_plugin]    Function Calls: ['get_weather']
[logging_plugin] 🔧 TOOL STARTING
[logging_plugin]    Tool Name: get_weather
[logging_plugin]    Arguments: {'city': 'London'}
[logging_plugin] 🔧 TOOL COMPLETED
[logging_plugin]    Result: {'status': 'ok', 'report': 'The weather in London is 15C and drizzling.'}
[logging_plugin] 📢 EVENT YIELDED
[logging_plugin]    Function Responses: ['get_weather']
[logging_plugin] 🧠 LLM REQUEST
[logging_plugin] 🧠 LLM RESPONSE
[logging_plugin]    Content: text: 'The weather in London is currently 15°C and drizzling.'
[logging_plugin]    Token Usage - Input: 228, Output: 15
[logging_plugin] 📢 EVENT YIELDED
[logging_plugin]    Final Response: True
[logging_plugin] 🤖 AGENT COMPLETED
[logging_plugin] ✅ INVOCATION COMPLETED
```

</details>

> [!IMPORTANT]
> **What it means.** That is the full agentic loop, in order: the model saw the
> tools and chose `get_weather`, the tool ran with `{'city': 'London'}` and
> returned its report, the model was called a second time with that result and
> produced the final text, and the run ended. Two model calls, one tool call, and
> their token costs (167 plus 16 to decide the call, 228 plus 15 to write the
> answer), all without parsing DEBUG. This is the view you want when a tool is
> called with the wrong arguments, or not called when it should be.

**What you will not see.** `LLM REQUEST` prints the model, the first 200
characters of the system instruction, and the tool names, but not the
conversation contents. The source removed that on purpose:

```python
# Note: Content logging removed due to type compatibility issues
# Users can still see content in the LLM response
```

So the exact prompt sent to the model is still a DEBUG or `DebugLoggingPlugin`
job, which is what 3.3 is for.

> [!WARNING]
> **The catch that decides where you use it.** `LoggingPlugin` writes with
> `print()` and ANSI color codes, **not** through the `logging` module. That is
> perfect in a terminal and wrong for a deployed service: it ignores your
> handlers, levels, and formatters, and the color bytes corrupt a JSON log line.
> Use it for local debugging. When you need this information *in production*, use
> the structured plugin in Part 4 instead. The next section shows exactly what
> that catch looks like once the same script runs on Cloud Run.

---

### 3.2 LoggingPlugin on Cloud Run

> [!TIP]
> **Optional. Why you are here.** You would not deploy `LoggingPlugin` to a real
> service; this section exists only to satisfy the natural curiosity about what
> Cloud Run does with a print-based plugin, and the answer turns the 3.1 callout
> from a claim into evidence. It is the same move as 1.4: deploy the unmodified
> script as a Cloud Run Job, run it, and read back what Cloud Logging did with each
> line.

[deploy/deploy_plugin_job.sh](../deploy/deploy_plugin_job.sh) builds one image that
can run either plugin example; the script to run is the Job argument, and
`LOG_LEVEL` is an environment variable, so you can change the framework level
between runs without rebuilding. Example 03 configures no logging of its own, so
`LOG_LEVEL` controls only the framework logger (stream 2), never the plugin.

**👉 Do this.** Deploy and run once at INFO, then run again at WARNING:

```bash
export PROJECT_ID=your-project REGION=us-central1
SCRIPT=examples/03_logging_plugin.py ./deploy/deploy_plugin_job.sh   # deploys adk-plugin-job, runs at INFO
gcloud run jobs execute adk-plugin-job \
  --project="$PROJECT_ID" --region="$REGION" \
  --update-env-vars=LOG_LEVEL=WARNING --wait
```

Then read the plugin's own lines, and separately the framework's, back:

```bash
# The plugin narration (stdout):
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-plugin-job"
   textPayload:"logging_plugin"' \
  --project="$PROJECT_ID" --limit=10 \
  --format='value(severity,textPayload)' --freshness=15m

# The framework lines (stderr):
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-plugin-job"
   textPayload:"google_adk"' \
  --project="$PROJECT_ID" --limit=10 \
  --format='value(severity,textPayload)' --freshness=15m
```

**Expected output** — two things worth stopping on.

First, the narration is unchanged by the level. Both the INFO run and the
WARNING run carry the full `[logging_plugin]` narration; the WARNING run just has
no `google_adk` lines next to it. The framework query returns rows for the INFO
run and nothing for the WARNING run:

```console
INFO - google_adk.google.adk.plugins.plugin_manager - Plugin 'logging_plugin' registered.
INFO - google_adk.google.adk.models.google_llm - Sending out request, model: gemini-3.7-flash, ...
INFO - google_adk.google.adk.models.google_llm - Response received from the model.
```

Second, the narration reaches the cloud as raw terminal bytes. The severity
column is blank (Default) for every plugin line, and the ANSI codes arrive
literally in the payload:

```console
<no severity>  ^[[90m[logging_plugin] 🔧 TOOL STARTING^[[0m
<no severity>  ^[[90m[logging_plugin]    Arguments: {'city': 'London'}^[[0m
```

> [!IMPORTANT]
> **What it means, finding one: the plugin is independent of the level dial.**
> Turning stream 2 down to WARNING removed the framework's lifecycle lines and left
> the plugin narration completely intact, because the plugin never goes through
> `logging`. That is exactly what makes it great in development, and exactly why it
> is the wrong tool in production: you cannot turn it down without deleting it from
> the code.

> [!IMPORTANT]
> **What it means, finding two: the narration is not queryable.** Every plugin
> line lands on stdout with Default severity and its grey ANSI codes embedded in
> the text. It is readable in the console, but nothing in it is a field you can
> filter, alert on, or group. (The `google_adk` lines have the same problem 1.4
> found: they are on stderr and still come through as Default, not ERROR.) Making
> this information queryable is the job of Part 4, which feeds the same hook data
> through the `logging` module instead of `print()`.

Tear down when you are done:

```bash
gcloud run jobs delete adk-plugin-job --project="$PROJECT_ID" --region="$REGION" --quiet
```

---

### 3.3 DebugLoggingPlugin: capture one whole turn to a file

> [!NOTE]
> **Why.** Sometimes one specific turn misbehaves and you want the complete,
> inspectable record to diff or attach to a bug report, not a stream you have to
> watch live.

```python
from google.adk.plugins import DebugLoggingPlugin
plugin = DebugLoggingPlugin(output_path="adk_debug.yaml")
```

**How it differs from `LoggingPlugin`.** Both subclass `BasePlugin` and override
the same hooks, but almost everything else is opposite:

| | `LoggingPlugin` | `DebugLoggingPlugin` |
|---|---|---|
| Sink | `print()` to stdout | a YAML file |
| When it writes | immediately, at every hook | buffered in memory, written once per invocation in `after_run_callback` |
| Detail | truncated; no request contents | full request contents, config, tool list, responses, session state |
| Redaction | none | credential models, secret-named keys, private-key blocks, all `temp:` state |
| File safety | not applicable | created `0600`; warns once if an existing file is wider |
| Own diagnostics | none | emits real `logging` warnings and errors |

Its constructor exposes the knobs the terminal plugin does not have, all
keyword-only:

```python
def __init__(
    self,
    *,
    name: str = "debug_logging_plugin",
    output_path: str = "adk_debug.yaml",
    include_session_state: bool = True,
    include_system_instruction: bool = True,
):
```

Where `LoggingPlugin` formats a line and prints it, this plugin records the
request as structured data. Its `before_model_callback` keeps the whole thing:

```python
request_data = {
    "model": llm_request.model,
    "content_count": len(llm_request.contents),
    "contents": [self._serialize_content(c) for c in llm_request.contents],
}
if llm_request.tools_dict:
    request_data["tools"] = list(llm_request.tools_dict.keys())
self._add_entry(callback_context.invocation_id, "llm_request", **request_data)
```

Nothing is written until the invocation ends. `after_run_callback` dumps the
buffered entries as one YAML document, and it takes care to create the file
readable only by its owner:

```python
fd = os.open(self._output_path,
             os.O_WRONLY | os.O_CREAT | os.O_APPEND, _OUTPUT_FILE_MODE)  # 0o600
with os.fdopen(fd, "a", encoding="utf-8") as f:
    f.write("---\n")
    yaml.dump(output_data, f, default_flow_style=False,
              allow_unicode=True, sort_keys=False, width=120)
```

**👉 Do this**, then open the file it writes:

```bash
.venv/bin/python examples/04_debug_plugin.py
cat adk_debug.yaml
```

Example 04 passes `include_session_state=True` and
`include_system_instruction=True` explicitly. Both are already the defaults; they
are written out so you can see the knobs exist.

**Expected output** — one YAML document for the invocation, a list of timestamped
entries:

```console
- timestamp: '2026-09-03T23:54:59.413524'
  entry_type: llm_request
  data:
    model: gemini-3.7-flash
    contents:
    - role: user
      parts:
      - text: What's the weather in a city you don't know, like Paris?
    tools:
    - get_weather
```

The `entry_type` values, in order, trace the same lifecycle the terminal plugin
narrates: `invocation_start`, `agent_start`, `llm_request`, `llm_response`,
`event`, `tool_call`, `tool_response`, `event`, a second `llm_request` and
`llm_response`, `event`, `agent_end`, `session_state_snapshot`,
`invocation_end`.

> [!IMPORTANT]
> **What it means.** It is the full turn on disk: exact prompt, system instruction,
> tool arguments, tool results, token counts, and session state. Two properties
> matter. It is buffered, so nothing reaches the file until the invocation
> completes; if the process dies mid-turn, that turn is lost. And it redacts by
> design, but broadly:

> [!NOTE]
> That last rule blanks all temporary state, not
> only credentials, so an intermediate value passed between agents under a
> `temp:` key reads as `[REDACTED]` here.

The file still holds full prompt content, so it is created `0600` and should be
treated as sensitive. This is a debugging capture, not a log sink you leave
running. Example 04 also reads its output path from a `DEBUG_OUTPUT` environment
variable when one is set, which the next section uses to redirect the capture off
the container.

---

### 3.4 DebugLoggingPlugin on Cloud Run

> [!TIP]
> **Optional. Why you are here.** Like 3.2, this is a curiosity-driven detour, not
> a step you need. You would not run `DebugLoggingPlugin` on Cloud Run in practice,
> but doing it once teaches a real lesson about file-writing tools in ephemeral
> containers. 3.3 wrote a file; a Cloud Run Job's filesystem is thrown away when
> the execution ends. So where does the capture go?

**👉 Do this**, part one, the naive deploy:

```bash
SCRIPT=examples/04_debug_plugin.py ./deploy/deploy_plugin_job.sh   # deploys adk-debug-plugin-job
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-debug-plugin-job"' \
  --project="$PROJECT_ID" --limit=20 \
  --format='value(severity,textPayload)' --freshness=15m
```

**Expected output** — the script's two `print()` lines and nothing resembling the
YAML:

```console
FINAL ANSWER: I do not have weather data for Paris.
Full invocation captured to: /app/adk_debug.yaml
WARNING - google_adk.google.adk.plugins.debug_logging_plugin - No debug state for invocation e-..., skipping entry
```

The file was written to `/app/adk_debug.yaml` inside the container and discarded
with it. (The `skipping entry` warning is a harmless ADK ordering quirk: the
plugin's `on_user_message_callback` fires before `before_run_callback` creates
the per-invocation buffer, so the first entry is dropped. Notice it is a real
`logging` record on stderr, unlike anything `LoggingPlugin` emits.)

> [!IMPORTANT]
> **What it means.** A file-writing plugin needs a filesystem that outlives the
> execution. Cloud Run can mount a Cloud Storage bucket as a volume, and example 04
> already reads its path from `DEBUG_OUTPUT`.

**👉 Do this**, part two, mount a bucket:

```bash
export BUCKET="${PROJECT_ID}-adk-debug"   # any bucket you own; created in $REGION if missing
MOUNT=1 SCRIPT=examples/04_debug_plugin.py ./deploy/deploy_plugin_job.sh
gcloud storage cat "gs://$BUCKET/adk_debug.yaml" | head -40
```

With `MOUNT=1` the deploy script mounts `$BUCKET` at `/mnt/out` and sets
`DEBUG_OUTPUT=/mnt/out/adk_debug.yaml` on the Job.

**Expected output** — the same YAML document as 3.3, now read back from the bucket,
with the full `entry_type` sequence intact. Check Cloud Logging for one more
line the plugin emits about the file it just wrote:

```console
WARNING - google_adk.google.adk.plugins.debug_logging_plugin - Debug output file /mnt/out/adk_debug.yaml is readable beyond its owner and holds whole prompts and responses; restrict it to mode 600.
```

> [!IMPORTANT]
> **What it means.** The plugin behaved exactly as on your laptop; only the disk
> changed. The mode warning is the plugin doing its job: the Cloud Storage FUSE
> mount reports a mode wider than `0600`, so the plugin cannot guarantee the file
> is owner-only and says so, through the `logging` module, on stderr. Two cautions
> follow from that. The capture now lives in a bucket and still holds full prompts,
> so bucket IAM is your new `0600`. And this is still a debugging capture, not a
> log pipeline; if you find yourself running it routinely in the cloud, you want
> the structured plugin in Part 4 instead.

> [!TIP]
> A quick alternative, if you only need the capture once and do not want a
> bucket: have the script `cat` the file to stdout at the end, and it lands in
> Cloud Logging as one large text payload. It works, but it throws away the
> "file, not stream" property that made the plugin worth using.

Tear down when you are done:

```bash
gcloud run jobs delete adk-debug-plugin-job --project="$PROJECT_ID" --region="$REGION" --quiet
```

---

### 3.5 Plugin or level dial?

> [!NOTE]
> **Why you are here.** You have now seen both plugins, locally and deployed. When
> should you reach for one instead of just turning the `google_adk` level up? The
> short answer: when you want structured facts about the agent's steps rather than
> the framework's own log prose.

Built-in ADK logging is text lines under `google_adk`, at whatever level you set.
A plugin hooks the same lifecycle but receives objects, at named points, before
those lines are ever formatted. That difference buys four things:

| Benefit | What it means in practice |
|---|---|
| Objects, not strings | `after_model_callback` receives an `LlmResponse` with `usage_metadata`; you read token counts as numbers, never parse a DEBUG dump |
| Independent of the level | 3.2 proved it: WARNING silenced the framework and the plugin narration kept going |
| One registration, app-wide | a plugin fires for every agent and tool in the `App`; a per-agent callback has to be wired onto each agent |
| You own the sink | the same hook data feeds `print()` (3.1), a YAML file (3.3), JSON `logging` records (Part 4), or BigQuery |

What the level dial still does better: DEBUG shows the framework's own internals,
the wire-level request, HTTP retries, and session-service work, none of which
have plugin hooks. The two are complementary, not rivals.

Three cases where a plugin is the right call:

1. **A tool is getting the wrong arguments in development.** Run the framework at
   WARNING so its lines are quiet, attach `LoggingPlugin`, and watch the
   `Arguments:` lines. You see the tool calls and nothing else.
2. **You need a reproducible bug report.** Attach `DebugLoggingPlugin`, reproduce
   the turn, and attach the YAML. Or capture one document before a prompt change
   and one after, and diff them. From a Cloud Run Job, that means the mounted
   bucket from 3.4.
3. **You are watching token cost while tuning a prompt.** Read `Token Usage` per
   model call from `LoggingPlugin`, or `usage_metadata` from the YAML, with no
   formatter to write. When you want those numbers queryable in production, Part
   4 turns the same hook into structured log fields.

---

← Prev: [2. Access logs](02-access-logs.md) · [Tutorial index](../TUTORIAL.md) · Next: [4. Production logging](04-production.md) →

