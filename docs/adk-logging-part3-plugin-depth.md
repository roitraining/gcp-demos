# Plan: deepen Part 3 of the ADK logging tutorial

Tutorial: `ai/adk/logging/TUTORIAL.md`, lines 761-851 (Part 3). Goal: explain
how the two built-in plugins actually work, using the real source from
`google-adk 2.8.0` (`.venv/lib/python3.13/site-packages/google/adk/plugins/`),
take each plugin script to Cloud Run as a Job the way 1.4 did, and say when a
plugin beats the level dial. Keep the tutorial's
"Why you are here / Do this / You will see / What it means" rhythm.

## The asks, restated

| # | Ask | Proposed shape |
|---|---|---|
| 1 | 3.1: how `LoggingPlugin` works, default config, real snippet, expected behavior | "How it works" block between the wiring snippet and **Do this**, a full (untrimmed) console block, and a "what you will not see" note |
| 2 | After 3.1: deploy example 03 as a Cloud Run Job and test it like 1.4 | New **3.2 LoggingPlugin on Cloud Run** |
| 3 | 3.2 (now 3.3): how `DebugLoggingPlugin` differs, with snippets | Comparison table plus three short source snippets (constructor, capture, write) |
| 4 | After that: deploy example 04 as a Cloud Run Job and test it | New **3.4 DebugLoggingPlugin on Cloud Run** |
| 5 | Benefits of a plugin over built-in ADK logging, with use cases | New **3.5 Plugin or level dial?** |

## New Part 3 layout

| Section | Content | Status |
|---|---|---|
| 3.1 LoggingPlugin: one line to wire up | existing, expanded (ask 1) | edit |
| 3.2 LoggingPlugin on Cloud Run | new (ask 2) | new |
| 3.3 DebugLoggingPlugin: capture one whole turn to a file | existing 3.2, expanded (ask 3) | renumber, edit |
| 3.4 DebugLoggingPlugin on Cloud Run | new (ask 4) | new |
| 3.5 Plugin or level dial? | new (ask 5) | new |

Nothing outside Part 3 references "3.1" or "3.2" by number (checked), so the
renumbering touches only Part 3 headings and the "How to choose" table.

## Decisions / assumptions (review these)

- **D1: source snippets are quoted from the installed 2.8.0 package**, trimmed
  but not paraphrased, and cited as `google/adk/plugins/logging_plugin.py`.
- **D2: the "why" goes in 3.5, not inside 3.1**, so **Do this** stays near the
  top of 3.1 and the "How to choose" table has something to point back to.
- **D3: re-run examples 03 and 04 locally** to capture untrimmed output and
  the YAML `entry_type` list. Two runs.
- **D4: example 04 keeps its explicit keyword arguments.** Both are the
  defaults; the text says they are shown so you know the knobs exist.
- **D5: one new Dockerfile and one new deploy script for both jobs**, instead
  of touching 1.4's `Dockerfile.job` / `deploy_job.sh`. The 1.4 Dockerfile bakes
  `01_log_levels.py` into `ENTRYPOINT`, and 1.4's text relies on
  `--args=warning` at execute time. Changing that to a generic entrypoint
  would rewrite 1.4. New files:
  - `deploy/Dockerfile.plugin_job`: same base as `Dockerfile.job`, copies all
    of `examples/` and `demo_agent/`, `ENTRYPOINT ["python"]`. The script path
    is the Job argument.
  - `deploy/deploy_plugin_job.sh`: copy of `deploy_job.sh` with
    `SCRIPT=examples/03_logging_plugin.py|examples/04_debug_plugin.py`
    selecting the script and `JOB` defaulting to `adk-plugin-job` /
    `adk-debug-plugin-job` from it. Passes `--args="$SCRIPT"` at deploy time.
    Reads `PROJECT_ID` (required), `REGION` (default `us-central1`), and
    `MODEL_LOCATION` (default `global`) exactly as `deploy_job.sh` does.
    Optional `LOG_LEVEL` and `BUCKET` (see D7). No project, region, or
    bucket name appears in the script, the Dockerfile, or the tutorial
    commands; only in the `export` line the reader types.
  Alternative: extend `deploy_job.sh` with a `SCRIPT=` switch. Rejected: it
  would carry two Dockerfiles and two entrypoint conventions in one script.
- **D6: the level test in 3.2 uses the `LOG_LEVEL` env var already read by
  `demo_agent/agent.py`** (added for 1.6). Example 03 configures no logging
  itself, so setting `LOG_LEVEL=INFO` turns stream 2 on and `LOG_LEVEL=WARNING`
  turns it off, with the plugin narration untouched either way. That is the
  1.4 experiment (INFO run, then WARNING run) applied to a plugin, and the
  observed proof for 3.5's "independent of the level" row. Per-execution
  override: `gcloud run jobs execute ... --update-env-vars=LOG_LEVEL=WARNING`.
- **D7: 3.4's finding is that the file is gone; the fix is a Cloud Storage
  volume.** A Job's filesystem is discarded when the execution ends, so the
  YAML written to `/app/adk_debug.yaml` never reaches you, and Cloud Logging
  only holds the two `print()` lines. The section shows that first, then
  mounts a bucket (`--add-volume=name=out,type=cloud-storage,bucket=$BUCKET`
  plus `--add-volume-mount=volume=out,mount-path=/mnt/out`) and points the
  plugin at it. Requires one small change to example 04: read the output path
  from `DEBUG_OUTPUT` when set, default unchanged. Alternative: `cat` the
  file to stdout at the end of the script so it lands in Cloud Logging.
  Rejected as the primary path because it undoes the "file, not stream"
  lesson, but mention it as the quick hack.
- **D8: project, region, and bucket come from the environment.** The
  tutorial's `export PROJECT_ID=... REGION=...` convention from 1.4 carries
  over, plus `BUCKET`. When `BUCKET` is unset in 3.4, the script derives
  `${PROJECT_ID}-adk-debug` and creates it in `$REGION` if it does not exist.
  The verification runs use whatever I export in my shell (the same project
  the 1.4-1.7 runs used); the project name appears only in the "Verification
  status" section, as a record of what was run, never in a command. Console
  blocks with project-specific output get the project masked the way 1.4
  does (`projects/.../logs/...`). Cost: a few Job executions and one small
  object.
- **D9: do not claim `adk web` / `adk run` support for plugins** unless a
  quick grep of the installed `google/adk/cli` confirms it.

## Ask 1: 3.1 additions

### 1a. How the plugin is invoked (new block after the wiring snippet)

Three facts, each one or two sentences, then a short table:

1. `BasePlugin` defines 14 async hook methods (`on_user_message_callback`,
   `before_run_callback`, `on_event_callback`, `after_run_callback`,
   `before/after_agent_callback`, `before/after_model_callback`,
   `before/after_tool_callback`, three error hooks, `close`). Every one
   returns `None` by default. A plugin overrides the hooks it cares about.
2. `App(plugins=[...])` hands the list to a `PluginManager`. At each lifecycle
   point the runner calls the matching `run_*_callback`, which walks the
   plugins in registration order. Plugins run **before** agent callbacks.
3. Early exit: if any hook returns a non-`None` value, remaining plugins and
   agent callbacks for that point are skipped and the value is used instead
   (a `before_tool_callback` returning a dict replaces the tool result).
   `LoggingPlugin` returns `None` from every hook, so it is a pure observer.

Quote the `PluginManager` docstring sentence on early exit (lines 70-74).

### 1b. What "no arguments" configures

The only constructor parameter is `name`:

```python
def __init__(self, name: str = "logging_plugin"):
    super().__init__(name)
```

| Setting | Value | Where |
|---|---|---|
| Prefix | `[logging_plugin]` (the `name`) | `_log` |
| Sink | `print()` to stdout, grey ANSI (`\033[90m`) | `_log` |
| Level / handler / formatter | none; the `logging` module is never touched | whole file |
| Text and system-instruction truncation | 200 chars | `_format_content`, `before_model_callback` |
| Tool args and results truncation | 300 chars | `_format_args` |

Quote `_log`:

```python
def _log(self, message: str) -> None:
    # ANSI color codes: \033[90m for grey, \033[0m to reset
    formatted_message: str = f"\033[90m[{self.name}] {message}\033[0m"
    print(formatted_message)
```

Point: `--log_level` cannot reach this output, and neither can a
`dictConfig`. This is the mechanism behind the existing "catch" callout,
which stays as is and now gets its evidence in 3.2.

### 1c. One hook, end to end

Quote `before_tool_callback` (the source of the `TOOL STARTING` block) so the
reader can map source lines to output lines:

```python
async def before_tool_callback(self, *, tool, tool_args, tool_context):
    self._log(f"🔧 TOOL STARTING")
    self._log(f"   Tool Name: {tool.name}")
    self._log(f"   Agent: {tool_context.agent_name}")
    self._log(f"   Function Call ID: {tool_context.function_call_id}")
    self._log(f"   Arguments: {self._format_args(tool_args)}")
    return None
```

### 1d. Expected behavior: the full sequence

Replace the trimmed console block with the full capture from a fresh run of
example 03, then a numbered sequence for one tool-calling turn:

1. `🚀 USER MESSAGE RECEIVED` (invocation, session, user, app, root agent)
2. `🏃 INVOCATION STARTING`
3. `🤖 AGENT STARTING`
4. `🧠 LLM REQUEST` (model, agent, system instruction, available tools)
5. `🧠 LLM RESPONSE` with `function_call: get_weather` and token usage
6. `📢 EVENT YIELDED` (function call event)
7. `🔧 TOOL STARTING` / `🔧 TOOL COMPLETED`
8. `📢 EVENT YIELDED` (function response event)
9. second `🧠 LLM REQUEST` / `🧠 LLM RESPONSE` with `text: '...'`
10. `📢 EVENT YIELDED` with `Final Response: True`
11. `🤖 AGENT COMPLETED`, `✅ INVOCATION COMPLETED`

Confirm the order from the run before writing it.

**What you will not see.** `LLM REQUEST` prints the model, the first 200
characters of the system instruction, and the tool names, but **not** the
conversation contents. The source says why:

```python
# Note: Content logging removed due to type compatibility issues
# Users can still see content in the LLM response
```

So the exact prompt is still a DEBUG-level or `DebugLoggingPlugin` job. This
sets up 3.3.

## Ask 2: new 3.2 LoggingPlugin on Cloud Run

**Why you are here.** 3.1's callout says `print()` output ignores your logging
config. On your laptop that is invisible. In the cloud it decides what Cloud
Logging receives. Same move as 1.4: deploy the unmodified script as a Job,
run it twice, read back severity and payload.

**Do this.**

```bash
export PROJECT_ID=your-project REGION=us-central1
SCRIPT=examples/03_logging_plugin.py ./deploy/deploy_plugin_job.sh   # deploys adk-plugin-job, executes once
gcloud run jobs execute adk-plugin-job \
  --project="$PROJECT_ID" --region="$REGION" \
  --update-env-vars=LOG_LEVEL=WARNING --wait
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-plugin-job"' \
  --project="$PROJECT_ID" --limit=60 \
  --format='table(severity,textPayload)' --freshness=15m
```

First execution runs with `LOG_LEVEL=INFO` (set by the deploy script), the
second with `WARNING`.

**You will see** (predicted; replace with the real capture):

- Both executions carry the full `[logging_plugin]` narration. The WARNING
  execution has no `INFO - google_adk...` lines; the INFO execution
  interleaves them with the narration.
- Every narration line is filed with Default severity. It is on stdout, so
  the stderr question from 1.4 does not even arise.
- The ANSI bytes arrive in `textPayload` as literal escape sequences. Confirm
  the exact rendering (`\x1b[90m`, `[90m`, or stripped) from the run; whatever
  it is, the point is that the terminal coloring is now noise in the payload.
- Burst grouping: several narration lines may share one entry (same note as
  1.4).

**What it means.** Two findings that mirror 1.4:

1. The plugin is independent of the level dial. Turning stream 2 to WARNING
   changed nothing about the narration, because the plugin never goes
   through `logging`. Good in dev, and exactly why it is the wrong tool here:
   you cannot turn it down in production without removing it.
2. The narration reaches Cloud Logging as prose with color codes and Default
   severity. It is readable in the console, but nothing in it is a field you
   can query or alert on. Part 4 makes the same hooks emit structured records.

Add the same "Tear down" line as 1.4 (`gcloud run jobs delete adk-plugin-job`).

## Ask 3: 3.3 additions (existing 3.2, renumbered)

### 3a. Comparison table (right after the "Why")

| | `LoggingPlugin` | `DebugLoggingPlugin` |
|---|---|---|
| Sink | `print()` to stdout | YAML file, one document per invocation, appended with `---` |
| When it writes | immediately, at every hook | buffers entries in memory per invocation; writes once in `after_run_callback` |
| Detail | truncated (200 / 300 chars); no request contents | full request contents, generation config, tool list, responses, session state snapshot |
| Redaction | none | credential models, secret-named keys, armored private-key blocks, all `temp:` state |
| File safety | n/a | created `0600`; warns once if an existing file is wider than owner-only |
| Constructor | `name` only | keyword-only: `name`, `output_path`, `include_session_state`, `include_system_instruction` |
| Own diagnostics | none | `logging` warnings/errors under `google_adk.google.adk.plugins.debug_logging_plugin` |
| Failure mode | none | a write failure is logged, never raised; the turn still completes |

### 3b. Snippets

Constructor, showing defaults and the keyword-only signature:

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

Capture, from `before_model_callback`, to show it records the whole request
as data rather than a formatted line (contrast with 1c):

```python
request_data = {
    "model": llm_request.model,
    "content_count": len(llm_request.contents),
    "contents": [self._serialize_content(c) for c in llm_request.contents],
}
if llm_request.tools_dict:
    request_data["tools"] = list(llm_request.tools_dict.keys())
...
self._add_entry(callback_context.invocation_id, "llm_request",
                agent_name=callback_context.agent_name, **request_data)
```

Write, from `after_run_callback`: the `0600` create, the append, the YAML
document separator:

```python
fd = os.open(self._output_path,
             os.O_WRONLY | os.O_CREAT | os.O_APPEND, _OUTPUT_FILE_MODE)  # 0o600
with os.fdopen(fd, "a", encoding="utf-8") as f:
    f.write("---\n")
    yaml.dump(output_data, f, default_flow_style=False,
              allow_unicode=True, sort_keys=False, width=120)
```

### 3c. Prose additions

- Buffered, not streamed: nothing appears in the file until the invocation
  ends. If the process dies mid-turn, that turn is lost.
- List the `entry_type` values in the order they appear in the captured file
  (confirm from the run).
- The `temp:` rule blanks all temporary state, not only credentials. Quote
  the docstring sentence.
- Example 04's explicit `include_*=True` arguments are the defaults (D4).
- Example 04 gains `DEBUG_OUTPUT` (D7). One line in the text: "the path comes
  from `DEBUG_OUTPUT` when set, so 3.4 can point it at a mounted bucket."

## Ask 4: new 3.4 DebugLoggingPlugin on Cloud Run

**Why you are here.** 3.3 wrote a file. A Cloud Run Job's filesystem is
thrown away when the execution ends. So where does the capture go?

**Do this**, part one, the naive deploy:

```bash
SCRIPT=examples/04_debug_plugin.py ./deploy/deploy_plugin_job.sh   # deploys adk-debug-plugin-job, executes once
gcloud logging read \
  'resource.type="cloud_run_job" resource.labels.job_name="adk-debug-plugin-job"' \
  --project="$PROJECT_ID" --limit=20 \
  --format='table(severity,textPayload)' --freshness=15m
```

**You will see** (predicted): only the script's two `print()` lines,
`FINAL ANSWER: ...` and `Full invocation captured to: /app/adk_debug.yaml`,
plus `Container called exit(0)`. No narration (this plugin prints nothing), no
YAML. The file was written and then discarded with the container.

**What it means.** A file-writing plugin needs a filesystem that outlives the
execution. Cloud Run can mount a Cloud Storage bucket as a volume.

**Do this**, part two, the bucket mount:

```bash
export BUCKET="${PROJECT_ID}-adk-debug"   # any bucket name you own; created in $REGION if missing
MOUNT=1 SCRIPT=examples/04_debug_plugin.py ./deploy/deploy_plugin_job.sh
gcloud storage cat "gs://$BUCKET/adk_debug.yaml" | head -40
```

With `MOUNT=1`, the script adds the volume flags for `$BUCKET` and sets
`DEBUG_OUTPUT=/mnt/out/adk_debug.yaml` on the Job. `PROJECT_ID` and `REGION`
are the same variables as every other deploy in this tutorial.

**You will see** the same YAML document as 3.3, read from the bucket. Also
check Cloud Logging for one extra line: the plugin's own
`logging.warning` about file mode, because Cloud Storage FUSE reports a mode
wider than `0600`. Example 04 configures no handler, so Python's last-resort
handler puts that warning on stderr. Predicted, confirm from the run; if it
fires, it is a good example of stream 2 speaking while the plugin itself is
silent.

**What it means.** The plugin behaved exactly as on your laptop; only the
disk changed. Two cautions: the file now holds full prompts in a bucket, so
bucket IAM is the new `0600`; and this is still a debugging capture, not a
log pipeline. If you find yourself doing this routinely, you want Part 4.

Quick hack, one sentence: `cat` the file at the end of the script and it
lands in Cloud Logging as one big text payload. Works, but throws away the
"file, not stream" property that made the plugin useful.

Verify live before writing: `O_APPEND` and `os.open` with a mode on the
gcsfuse mount, and whether the `0o077` warning actually fires. If append is
refused, fall back to the `cat` approach as the primary path and say why.

Tear down: delete the job, and the object if you want.

## Ask 5: new 3.5 Plugin or level dial?

### 5a. Benefits, tied back to the four streams

Built-in ADK logging (stream 2) is text lines under `google_adk` at a level.
A plugin gets **objects at semantic hook points**.

| Benefit | What it means in practice |
|---|---|
| Objects, not strings | `after_model_callback` receives `LlmResponse` with `usage_metadata`; you never parse a DEBUG dump for token counts |
| Independent of the level | 3.2 showed it: WARNING silenced stream 2 and the narration kept going |
| One registration, app-wide | fires for every agent and tool in the `App`; a per-agent callback needs wiring per agent |
| You own the sink | same hooks feed `print()` (3.1), YAML (3.3), JSON `logging` records (Part 4), or BigQuery |

Also say what built-in DEBUG still does better: the wire-level request, HTTP
retries, session-service work, none of which have plugin hooks. The two are
complementary.

### 5b. Use cases (three, one short paragraph each)

1. **Wrong tool arguments in dev.** Run at WARNING so stream 2 is silent,
   attach `LoggingPlugin`, watch `Arguments:` lines. Ties to 1c and 3.2.
2. **A reproducible bug report.** Attach `DebugLoggingPlugin`, reproduce the
   turn, attach the YAML. Or capture before and after a prompt change and
   diff the two documents. From a Job, that means the bucket in 3.4.
3. **Token cost while tuning a prompt.** `Token Usage` per model call from
   `LoggingPlugin`, or `usage_metadata` in the YAML, without writing a
   formatter. Bridges to Part 4, which makes the same numbers queryable.

### 5c. Update the "How to choose" table

No row changes. Add "see 3.5" to the `LoggingPlugin` and
`DebugLoggingPlugin` rows.

## Files touched

| File | Change |
|---|---|
| `ai/adk/logging/TUTORIAL.md` | Part 3 rewrite per above; "How to choose" back-refs; "Verification status" gains the 3.2 / 3.4 runs |
| `ai/adk/logging/deploy/Dockerfile.plugin_job` | new (D5) |
| `ai/adk/logging/deploy/deploy_plugin_job.sh` | new (D5, D7) |
| `ai/adk/logging/examples/04_debug_plugin.py` | `OUTPUT` from `DEBUG_OUTPUT` env var when set (D7) |
| `ai/adk/logging/README.md` | one line if it lists the deploy scripts (check) |

## Checklist

**Status: executed 2026-09-03. All items done; jobs torn down, bucket kept.**

- [x] Run `examples/03_logging_plugin.py` locally; save full console output
- [x] Run `examples/04_debug_plugin.py` locally; save `entry_type` sequence
- [x] Check `adk web` / `adk run` plugin loading in `google/adk/cli` (D9)
- [x] Write `Dockerfile.plugin_job` and `deploy_plugin_job.sh`
- [x] Add `DEBUG_OUTPUT` to example 04
- [x] Deploy and execute `adk-plugin-job` at INFO and WARNING; read logs back; save output
- [x] Deploy and execute `adk-debug-plugin-job` without bucket; read logs back
- [x] Redeploy with `MOUNT=1` (bucket derived from `PROJECT_ID`); `gcloud storage cat` the YAML; check for the mode warning
- [x] Write 3.1 (1a-1d), 3.2, 3.3 (3a-3c), 3.4, 3.5; renumber headings
- [x] Update "How to choose" back-refs and "Verification status"
- [x] Writing-guideline pass on the new text only
- [x] Verify every quoted snippet against the 2.8.0 source
- [x] Tear down both jobs (leave the bucket unless told otherwise)
- [x] Grep the new files and Part 3 for any literal project, region, or bucket name

## Size budget

About 220-260 added lines in `TUTORIAL.md`. If 3.5 grows past 40 lines, cut a
use case, not the table. 3.2 and 3.4 should each be shorter than 1.4.
