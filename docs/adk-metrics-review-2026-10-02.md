# ADK metrics tutorial review, 2026-10-02

**Scope:** everything under `ai/adk/metrics/`: the README, TUTORIAL.md, Setup, Scenarios, Parts 1 to 4, and the how-to-choose reference page. The review read the working tree on the `tracing-tutorial-wip` branch, including uncommitted changes.

**Versions checked against:** google-adk 2.8.0, google-genai 2.22.0 and bigquery-agent-analytics 0.5.2, as reported by `.venv/bin/pip show`.

**Method:** each part got three reviewers. One read it as a new student, checking writing and logic. One checked every factual claim against the installed SDK source and the public docs. One reran every demo the part asks the reader to run, on a dev project of its own.

**Path conventions:** file paths are relative to `ai/adk/metrics/`. A path starting with `adk/` means the installed ADK package, `.venv/lib/python3.13/site-packages/google/adk/`. Page numbers such as "2.4" refer to tutorial pages, and line numbers refer to the page named in each section's heading.

## Triage, 2026-10-02

This review read an older copy of the tutorial. Every finding was rechecked against `main` at `4ce1fa4` (after PRs #36, #37 and #40) and given a status:

| Status | Meaning |
|---|---|
| fixed on main | Already corrected on `main`; no change needed. |
| still real | Present on `main`; to be fixed on branch `adk-metrics-review-fixes`. |
| not applicable | No longer applies to the page as it stands. |
| done | Fixed on branch `adk-metrics-review-fixes`. |
| skipped: reason | Left as is, for the reason given. |

The finding tables carry a Status column. The top 10 and the inconsistencies carry a status too.

## Verdict

| Part | Demo results | State of the part |
|---|---|---|
| Setup and Part 1 | Every demo ran. Output had the same structure as the pages show; the numbers differ, which is expected from a live model. | Ready to publish once the pages agree on when the seventh metric appears and a few facts are corrected. |
| Part 2 | Every demo ran, with the same structure as the pages show. | Pages 2.4 and 2.5 explain the export mechanism incorrectly. Page 2.3's cleanup leaves a container image and a source archive behind. Page 2.2's expected output does not match what a fresh project shows. |
| Part 3 | Pages 3.5 and 3.6 fail when run as written, and page 3.7's query returns no data. | Most expected-output blocks are still placeholders marked `NEEDS-RUN`. Page 3.1's model-call latency figure is meaningless (see top finding 5). |
| Part 4 | The load script fails on every page, and commands on 4.1, 4.3 and 4.4 fail. | Cannot be followed as written. |

### Top 10 findings

1. **wrong.** `load/turns.sh` cannot send turns to the server in `examples/04_bq_plugin.py`. Every turn gets an HTTP 404 on pages 4.1 to 4.4, yet the script still ends by printing "good to go". *Status: fixed on main (the server has the session and `/run` routes); still real: `turns.sh` prints "good to go" after failed turns.*
2. **wrong.** Cloud Monitoring rejects `queries/dashboard.json` and `queries/alert-policy.json`, because both files use `//` as a JSON key to hold comments. This breaks pages 3.5 and 3.6. *Status: still real.*
3. **wrong.** The counter query on page 3.7 adds a `_total` suffix to the metric name. The Telemetry API never adds that suffix, so the query returns nothing. *Status: fixed on main.*
4. **wrong.** Part 3 hardcodes `export PROJECT=jwd-gcp-demos` in 10 places, so a reader's own project is ignored. *Status: still real.*
5. **wrong.** On page 3.1, the 95th-percentile model-call latency carries no information. The model-call histogram (`gen_ai.client.operation.duration`) uses OpenTelemetry's default bucket boundaries of 0, 5, 10, 25 seconds and up. With every call under 5 seconds, all calls land in the first bucket, and the "95th percentile" is just a point interpolated inside that 0 to 5 second range. "The model holds at 4.83 s" therefore says only "every call took under 5 seconds". *Status: still real.*
6. **wrong.** Several SQL queries and SDK calls in Part 4 fail: *Status: fixed on main.*
   - page 4.1 uses `rows` as a column alias, which is a reserved word in BigQuery;
   - page 4.3 reads `$.text` from the JSON, but the field is `$.text_summary`;
   - page 4.4 passes an invocation id to `get_trace()`, which expects a trace id;
   - page 4.4 uses the flags `--project` and `--dataset`, which do not exist.
7. **wrong.** On page 4.4, when a tool returns `{"status": "error"}` without raising an exception, the BigQuery plugin records the call as successful. The SDK's error rate therefore reads 0, not the 0.5 the page promises. For the same reason, the `v_tool_error` view on page 4.2 stays empty. *Status: still real: page 4.4 now explains it, but the 4.2 deep dive still says `v_tool_error` gets rows.*
8. **misleading.** Pages 1.1, 1.4, 2.2 and how-to-choose each say something different about the seventh metric, `gen_ai.invoke_workflow.duration`. In fact it appears only when an app uses ADK's newer `Workflow` primitive. *Status: still real.*
9. **misleading.** On page 2.5, Agent Runtime exports metrics at most once every 5 seconds, so the points from the last turn are lost when the run ends. The rerun exported 9 of 10 turns. The page says points leave as each turn completes. *Status: still real.*
10. **wrong.** Two Part 3 queries cannot show what their pages claim. Page 3.2 reads histogram buckets that count everything since the server started, not just the current scenario. Page 3.4 asks the reader to watch a value change across the run but uses an instant query, which returns a single number. *Status: still real.*

---

## Findings by file

**Severity tags**, from most to least serious: **wrong** (a reader following the page gets an error or a false belief), **misleading** (technically defensible but leads the reader to the wrong conclusion), **unclear** (a reader would have to guess what is meant), **style** (breaks the house style but does not hurt understanding). Within each file, findings are grouped by tag in the order wrong, style, misleading, unclear. The appendix lists the full set of standards the review applied.

### README.md

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 5–6 | "Part 1 runs entirely on your laptop against a real model" | "Entirely on your laptop" suggests no cloud account is needed. Part 1 calls Gemini through Vertex AI, which needs a Google Cloud project and credentials. | "Part 1 runs on your laptop and calls Gemini through Vertex AI. It needs a Google Cloud project, but not Cloud Monitoring or BigQuery." | done |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 63–71 | The Status section | It describes the tutorial's drafting progress (pages still marked `NEEDS-RUN`, a plan file in `docs/`). That is information for the author, not the reader. | Delete the Status section, along with the matching status sentences at lines 6–7 and 17–18. | done |
| 28–33 | The Files table lists `01_console_metrics.py`, `03_histogram_shape.py`, `02_two_attribute_sets.py`, `05_workflow_metrics.py`, `03_metrics_server.py`, `04_bq_plugin.py`, in that order | The number prefixes on the example files do not follow the order the pages use them in. Page 1.2 uses `03_`, then page 1.3 uses `02_`. Two different files share the prefix `03_`. A reader would expect the numbers to give the running order, and they don't. | Rename the example files so their numbers follow page order. Or, if renaming is too disruptive, add a "Used on page" column to the table and stop relying on the numbers. | done: added a "Used on" column; files not renamed |
| 41–61 | The Quick start section | The Quick start copies the first steps of the Setup page but leaves out `gcloud auth application-default login`. The example it then runs calls Vertex AI, which fails without those credentials. A reader who follows only the Quick start hits an authentication error. Keeping two copies of the setup steps also means they drift apart. | Replace the Quick start with one line: "Follow [Setup](tutorial/00-setup.md)." | done |

### TUTORIAL.md

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 3 | "This is a hands-on tutorial." | Filler: the sentence tells the reader nothing the title doesn't. | Start with what the reader does: "You run a small agent…". | done |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 57 | "Local, no cloud." | Part 1 does use the cloud: it calls a model on Vertex AI. What stays local is the metrics. | "Local: metrics never leave your laptop." | done |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 25 | "exported every N seconds" | "N" leaves the reader to guess the interval. | "exported on a timer (every 5 seconds with `--otel_to_cloud`)" | done |
| 42–46 | "project `jwd-gcp-demos`" … "See the tutorial plan for status." | The author's project id means nothing to a reader, and "the tutorial plan" is a file the reader never sees. | Drop the project id. Point the status sentence to the how-to-choose page, which lists what was verified. | done |

### tutorial/00-setup.md

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 14–110 | 8 code blocks the reader runs, none labeled **Command:** | The house style labels every runnable block so the reader can tell what to run from what to read. | Add the **Command:** labels. | done |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 124 | `"resource": { "attributes": { "service.name": "adk-metrics" } }` | The page presents this as real output, but a real run shows three resource attributes, not one: `service.instance.id`, `cloud.region` and `service.name`. | Show all three, or label the block "trimmed". | done |
| 129–135 | The `execute_tool.duration` datapoint shows one attribute, `gen_ai.agent.name` | Page 1.1 shows the same datapoint with three attributes. A reader comparing the two pages will think something changed. | Reuse page 1.1's block, or label this one "trimmed". | done |
| 85–86 | "Two latencies are the whole reason the tool and token distributions have shape." | This is false for tokens: page 1.2's token histogram gets its shape from London-only turns, which call only one tool. | "The two tools give later scenarios a second latency to vary." | done |
| 150–151 | The note on a 403 error: "a shell variable is overriding `.env`" | Two different variables name the project: `GOOGLE_CLOUD_PROJECT` in `.env` and `PROJECT_ID` in `env.sh`. The note doesn't say which one is overriding which, so the reader can't act on it. | At line 52, say: "Set `PROJECT_ID` to the same id as in `.env`. If both are set, the shell value wins." | done |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 8 and 15 | Line 8: "All commands run from this folder". Line 15: `cd ai/adk/metrics` | Line 8 says the reader is already in the folder, then line 15 changes into it from the repo root. | Introduce line 15 with "From the repo root:". | done |
| 90–96 | The `StatusAwareTool` code | This code is the lesson of page 1.3. Showing it here, before the reader has a reason to care, adds weight to Setup and duplicates page 1.3. | Remove it here; page 1.3 shows it. | done |

### tutorial/scenarios.md

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 35–48 | The section "The agent behind them" | It repeats the Setup page's "Meet the agent" section. | Keep one copy and link to it from the other page. | done |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 19–20 | "Scenario names are a fixed set, so they are safe as a metric attribute" | No metric carries the scenario name, so this sentence answers a question the reader never had, and suggests something that isn't true. | "The scenario name only selects what `load/turns.sh` sends. It is never recorded as a metric attribute." | done |
| 17–19 | "you run it under load with `load/turns.sh <scenario> [N]`" | The page lists eight scenarios, but `turns.sh` accepts only six. It exits with an error on `workflow` and `export-outage`. | Add: "`workflow` runs as a script (page 1.5). `export-outage` runs the `baseline` scenario against a deliberately misconfigured server." | done |
| 32–33 | "started without a valid metrics resource"; "the container series nests its children" | Both phrases only make sense if you already know what they describe. | "starts without `gcp.project_id`, so Cloud Monitoring rejects every batch with a 400 error"; "the outer agent's duration includes the durations of its sub-agents" | done |

### tutorial/part-1/index.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 13–14 | "with a console reader and no Google Cloud account" | Part 1 calls Vertex AI, which needs a Google Cloud account. | "with a console reader. No Cloud Monitoring or BigQuery is involved." | done |
| 1, 34 | `[← 0 · Setup](../00-setup.md)` | The reading order is Setup, then Scenarios, then Part 1. The "previous" link skips Scenarios. | `[← Scenarios](../scenarios.md)` | done |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 19 | "Each page here installs a console reader" | Page 1.2 uses an in-memory reader instead, so the sentence is not true for every page. | "Each page installs a metric reader." | done |

### tutorial/part-1/1.1-your-first-datapoint.md

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 12–15 | The "Why you are here" note names no scenario or question | This tutorial's convention is that every page's note names the scenario it runs and the operational question it answers. | "Scenario `baseline`: is the agent recording anything, and what did one turn cost?" | done |
| 142 | "operator question" | Elsewhere the tutorial says "operational question". Two terms for one idea make the reader wonder whether they differ. | "operational question" | done |
| 158–168 | The deep dive has no one-sentence summary and link in the page body | The house style gives each deep dive a summary sentence in the body that links down to it, so a reader knows it exists. | Add one sentence in the body, ending with `See [Why does the script need to flush?](#…)`. | done |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 88–90 | "that seventh metric stays silent until [1.5]" | This promises the seventh metric shows up on page 1.5. It doesn't: it needs ADK's newer `Workflow` primitive, and page 1.5 uses a `SequentialAgent`. | "that seventh metric needs ADK's newer `Workflow` primitive. Page 1.5 shows what a `SequentialAgent` records instead." | done |
| 98–101, 126 | "with its full field set"; attributes listed as "agent, model, token.type" | The real datapoint has six attributes, not three (`adk/telemetry/_metrics.py:556-575`): agent name, operation name, provider, request model, response model and token type. | Say "the fields this page uses", or list all six. | done |
| 19–20 | "The reader prints every histogram ADK recorded during the turn." | The reader writes to a file, not to the terminal. A reader looking at the terminal for the histograms won't find them. | "The reader writes every histogram ADK recorded during the turn to `out/metrics.json`." | done |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 42–72 | A single `console` code block holding both what the terminal prints and the contents of the JSON file | The reader can't tell where the terminal output ends and the file begins. | Split it into a console block, then a separate block headed "Contents of `out/metrics.json` (trimmed)". | done |
| 162–163 | "so that points are not collected too close together", citing `setup.py:96-103` | The sentence doesn't explain the real reason for the flush, and the citation is off by one line. | "ADK does not flush the meter provider when the process exits (`adk/telemetry/setup.py:96-104`), so the script calls `force_flush()` itself." | done |

### tutorial/part-1/1.2-reading-a-histogram.md

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 23, 61, 64, 74 | The step label "👉 Run ten turns…"; the heading "What a histogram is for"; the word "actually" in "actually felt"; a NOTE callout used for a side path | Four small breaks from house style: step labels use the `**👉 Do this.**` form; deep-dive headings are questions; "actually" is filler; a side path belongs in a TIP, not a NOTE. | Use `**👉 Run ten turns.**`, turn the heading into a question under `###` in Deep dives, drop "actually", and change the NOTE to a TIP. | done |
| 36–52 | The expected output leaves out the `asking turn N/10...` progress lines | The reader's terminal shows lines the page doesn't, which makes them doubt they ran the right thing. | Show the progress lines, or note "progress lines trimmed". | not applicable: the script erases its progress line with `\r` before printing, so a terminal shows none (the reviewer captured redirected stderr) |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 56–58 | "most calls sit in the 50-to-75 band with a tail reaching 100" | The bucket counts change from run to run. The page's own capture shows 3, 9 and 8 calls in three buckets; the rerun showed 1, 3, 15 and 1 in four. A reader whose run differs will think something is wrong. | "The largest share of calls sits in the 50 to 75 bucket. The exact split moves from run to run." | done |
| 63–67 | "On the chart above, a slow turn would raise a bar in a high bucket" | The chart above shows token counts, not durations. A slow turn doesn't change token counts. | "On a duration histogram, a slow turn would raise a bar in a high bucket." | done |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 36–52 | The 20 model calls are presented as one group | Each turn makes two different kinds of model call, and the page never says so. The reader can't explain why the histogram has the shape it does. | "Each turn makes two model calls: one that asks for the tool, and one that writes the answer. The histogram mixes both kinds." | done |

### tutorial/part-1/1.3-attributes-and-cardinality.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 128–131 | "which FunctionTool leaves returning None" | `FunctionTool` does detect errors, but only one kind: a response with a truthy `error` key (`adk/tools/function_tool.py:355-359`). The demo's tool returns a `status` field instead, which is why it goes unnoticed. The same wrong wording is in `demo_agent/agent.py:97-99`. | "FunctionTool flags only a response that has an `error` key, so a `status` field goes unnoticed." Fix the comment in `demo_agent/agent.py` too. | fixed on main |
| 111 | "(telemetry/_metrics.py:585-590)" | The cited lines don't contain the code the sentence describes. | `(adk/telemetry/_metrics.py:483-491, 504-520, 556-575)` | done |

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 12–16, 147 | The "Why you are here" note runs three sentences; the handoff to the next page sits after the deep dives | House style limits the note to two sentences and puts the handoff above the deep dives, where a reader on the main path will see it. | Cut the note to two sentences that name the `unknown-city` scenario, and move the handoff above `## Deep dives`. | done |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 57–72 | "a failed lookup returns before the tool does its work", with latency panels ranging from 0.02 to 0.64 seconds | The rerun showed `get_weather` takes 0.002 seconds whether the lookup succeeds or fails, so failure isn't faster. `get_forecast` sleeps before it checks the city, so it isn't faster on failure either. The panels look like captured output but are invented. | Delete the panels and the claim that failure makes the tool faster. Or capture a real `unknown-city` run and show that. | done: panels and the faster-failure claim removed |
| 84–87 | "`gen_ai.invoke_agent.duration` kept one series" | The claim is true, but nothing on the page shows it, so the reader has to take it on faith. | Cite the source: `adk/telemetry/_metrics.py:285-292`. | done |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 45–48, 121–124 | "See the deep dive"; "swap the reader for `install_console_reader()`…" | "See the deep dive" is not a link. The swap advice tells the reader to edit code without saying how. | Make "See the deep dive" a real link, and replace the swap advice with a command the reader can run. | done: the script now also writes `out/metrics.json`, and the deep dive opens it |

### tutorial/part-1/1.4-the-experimental-family.md

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 63–72 | The rerun with the variable unset has no Command label, expected output or callout | The reader is asked to run something but never told what they should see. | Make it **Step 2 — Turn it off.** and show the expected result: 6 metric names. | done |
| 38–48, 58–61 | The expected output is shown as a table instead of a code block; the WARNING runs three sentences | House style shows output as it appears in the terminal, and keeps a WARNING to one sentence. | Use an excerpt of the real terminal output, and cut the WARNING to one sentence. | done |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 13 | "The six metrics so far measure each model call." | Only two of the six are recorded per model call. The others are recorded per tool call or per agent turn, which is the tutorial's central idea. | "The six metrics so far are recorded per model call, per tool call, or per agent turn." | done |
| 74–75 | "where a seventh framework metric can finally appear" | Page 1.5 does not produce the seventh metric (see the page 1.1 finding above). | "Page 1.5 adds a second agent to show how agent-level metrics split by agent name." | done |
| 19 | "(telemetry/_instrumentation.py:289)" | The cited line isn't where the gate is checked. | `(adk/telemetry/context.py:116-118, adk/telemetry/_instrumentation.py:586-589)` | done |
| 70–71 | "The gate is a plain environment check" | The environment variable is only the default. A per-request `RunConfig` setting can also turn the metrics on. | "The environment variable is the default switch (`1` or `true`). A per-request `RunConfig` setting can also turn it on (`adk/telemetry/context.py:276-285`)." | done |

### tutorial/part-1/1.5-workflow-grain-metrics.md

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 63 | "(workflow/_node_runner.py, …)" | The citation has no line number. | `(adk/workflow/_node_runner.py:132)` | done |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 68–70 | "you will see a `DeprecationWarning` at construction" | The reader won't see it: `examples/05_workflow_metrics.py:28` silences the warning. | "`SequentialAgent` is deprecated in ADK 2.8.0 in favor of `Workflow`. The example silences the warning." | done |
| 54–56 | "children plus the sequencing between them, so it is roughly the sum" | The rerun gave 2.64 + 3.30 = 5.94 seconds, an exact sum. "Plus the sequencing" suggests extra overhead the data doesn't show. | "The outer agent's duration equals the sum of its two sub-agents' durations." | done |
| 13 | "This reference page adds" | Page 1.5 is a lesson page, not a reference page. | "This page adds" | done |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| title, 18 | "workflow-grain" in the title; the link text `SequentialAgent` pointing to a script | "Workflow-grain" is jargon, and it suggests the `Workflow` primitive, which this page does not use. Link text naming a class should not open a script file. | Retitle the page "Outer and inner agents", and use the script's path as the link text. | done |

### tutorial/part-2/index.md

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 11–31 | The "Why you are here" note runs three sentences, followed by three paragraphs | House style keeps the note to two sentences and the landing page to one paragraph. | Cut to two sentences and one paragraph. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 29–31 | "The last two pages are reference: your own server, then non-Google backends." and "Each page runs the `baseline` scenario" | Page 2.4 (your own server) is a hands-on lesson, not reference. Only page 2.6 is reference. | "Pages 2.1 to 2.5 each run `baseline` through a different export route and read the results back. Page 2.6 is a reference page for non-Google backends." | still real |

### tutorial/part-2/2.1-adk-web-otel-to-cloud.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 165–168 | "On Cloud Run and Agent Runtime the resource detector supplies both from the metadata server" | True for Cloud Run only. On Agent Runtime, ADK builds the resource from environment variables the runtime sets (`adk/telemetry/google_cloud.py:308-333`). | "On Cloud Run, the resource detector reads both from the metadata server. On Agent Runtime, ADK builds the resource from the runtime's environment variables." | still real |
| 101 | `export START=$(date -u -v-30M +%s)` | The `-v` flag exists only in the macOS (BSD) version of `date`. The command fails on Linux and in Cloud Shell. | `export END=$(date -u +%s)` then `export START=$((END - 1800))` | still real |

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| whole page | 923 words; the deep-dive heading is a statement, not a question | House style caps a page at 750 words and phrases deep-dive headings as questions. | Move the `plot_tokens.py` step into a deep dive, and retitle the deep dive "Why do metrics need `OTEL_RESOURCE_ATTRIBUTES`?" | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 31 | `adk web --otel_to_cloud ./` | In the rerun, a bare `adk` ran the copy installed in a different virtual environment (`ai/adk/.venv`), not this tutorial's. | Use `.venv/bin/adk`, as pages 2.3 and 2.5 do. | still real |
| 95–96, 110 | The PromQL response is written to `out/metrics.json` | Part 1 already uses that file for the metric reader's output, so this step overwrites it. | Write to `out/tokens.json`, and update `examples/plot_tokens.py` to read that file. | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 203–206 | "you get no new points … discards the process totals" | The deep dive states what happens during an export outage but never shows it. | Show the query and its result. The rerun saw the count stay at 20 after 5 turns sent during the outage. | still real |
| 75–94 | "two front doors"; "**Door 1 — …**", "**Door 2 — …**"; "That gap is the whole point." | "Front doors" is a metaphor for two ways to query the data. "That gap is the whole point" assumes the reader already knows what the gap is. | Label them "**Option A, Metrics Explorer.**" and "**Option B, PromQL API.**", and cut the "gap" sentence. | still real |
| 79–82 | Directions for Option A written as a paragraph | Clicking through a console is easier to follow one action at a time. | Make it a bulleted list, one action per bullet. | still real |
| 36–37, 168 | "the logging tutorial documents in its 5.2" | The reader may never have read the logging tutorial, and there is no link. | Link the page, or state the rule in one sentence here. | still real |
| 190–196 | The outage output ends with "good to go — the series are in Cloud Monitoring" | The load script prints this even while Cloud Monitoring rejects every batch, so the message is false here. The page doesn't point that out. | Call it out as a trap: the script reports success even though every batch was rejected. | still real: the page no longer shows the line, but `turns.sh` still prints it during an outage |

### tutorial/part-2/2.2-the-metric-catalog.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 45, 60–65 | `prometheus.googleapis.com/gen_ai.invoke_workflow.duration/histogram` … "present only because an earlier workflow run (1.5) created its descriptor" | Part 1 never exports anything to Cloud Monitoring, so page 1.5 can't have created this descriptor. The rerun on a fresh project listed six descriptors, not seven. | Show six descriptors, and add: "A seventh appears only if something in this project ran the `Workflow` primitive." | still real |
| 118–119 | The rows for the two `client.*` metrics list `gen_ai.response.model` and `error.type` as labels | The real labels are `gen_ai.system`, `gen_ai.request.model`, `gen_ai.operation.name` and `gen_ai.token.type` (`opentelemetry/instrumentation/google_genai/generate_content.py:946-973`). The rerun saw exactly those four. | Replace the label list with those four. | still real |
| 122–123 | The `inference_calls` and `tool_calls` rows | These rows have two cells in a three-column table, so the table renders incorrectly. | `\| …/inference_calls/histogram \| gcp.vertex.agent \| gen_ai.agent.name \|` | still real |

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 56, 68, 111, 128, 141 | Em dashes with spaces around them; a sentence fragment; links `[3.4]` and `[3.7]` that both open `part-3/index.md` | House style avoids em dashes outside step labels and needs full sentences. The links should open the pages they name. | Use commas, write the fragment as a full sentence, and point the links at pages 3.4 and 3.7. | still real: the 3.4 link is fixed; spaced em dashes and the 3.7 link remain |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 125–128 | "Every descriptor also carries `otel_scope_name` … (`gcp.vertex.agent`)" | Not every descriptor has that value. The two `client.*` metrics carry `opentelemetry.instrumentation.google_genai`. | "…`gcp.vertex.agent` for ADK's own metrics, and `opentelemetry.instrumentation.google_genai` for the two `client.*` metrics." | still real |
| 107–109 | "the client metrics come from the genai instrumentation scope, not ADK's meter" | This depends on how the agent is served. It holds when the genai instrumentation is active, as under `adk web` and `adk api_server` (`adk/cli/api_server.py:736-745`). Page 2.4's server records them under `gcp.vertex.agent`. | Add: "when the genai instrumentation is active, as under `adk web` and `adk api_server`. Page 2.4's server records them under `gcp.vertex.agent`." | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 15–16 | "No query language yet." | The page then runs a PromQL query. | "One PromQL lookup. Part 3 teaches the language." | still real |
| 20 | "The PromQL proxy has no `/series` endpoint" | The Cloud Monitoring docs say `/api/v1/series` supports GET requests, which contradicts this. | Check the claim. If it doesn't hold, reword to: "`metricDescriptors.list` lists which metrics exist without querying their values." | still real |

### tutorial/part-2/2.3-api-server-and-cloud-run.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 127–139 | The cleanup step deletes only the Cloud Run service | `adk deploy` also leaves a 133 MB container image in Artifact Registry and a source archive in `gs://run-sources-<project>-<region>`. The reader keeps paying to store both. | Add commands that delete the image and the source archive. | still real |

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 68–75 | The expected output leaves out the "waiting 10s" and "good to go" lines | The reader sees lines the page doesn't show. | Show them. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 118–119 | "A deployed ADK service needs the flag and nothing else" | It also needs the exporter packages in `requirements.txt`; without them the service crashes on startup. | "A deployed ADK service needs the flag and the exporter packages in its requirements, but no `OTEL_RESOURCE_ATTRIBUTES`." | still real |
| 113–117 | "the `400` that hit the laptop in 2.1" | The 400 error appeared only in page 2.1's deep dive. A reader who skipped it won't recognize the reference. | Say it occurred in page 2.1's deep dive, and link to it. | still real |
| 101–111 | `model calls/min ~10`, `turns/min ~5` shown in a console block | These look like captured output, but the rerun peaked at about 8 model calls, 4 turns and 4 tool calls per minute. | Capture real values, or label the block illustrative. | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 36, 59 | `$PROJECT_ID` and `$REGION` used without `source env.sh` | A reader in a new shell has neither variable set, so the commands fail or target the wrong project. | Add `source env.sh` to Step 1. | still real |
| 29–51 | Three side issues in the main body: the crash when exporter requirements are missing, `GOOGLE_CLOUD_LOCATION`, and "exits 0 on a failed build" | These are troubleshooting details that interrupt the main path. | Move them to Deep dives. The exit-code claim is confirmed at `adk/cli/cli_tools_click.py:2457`; cite it there. | still real |
| 50–53, 110 | "The curl in Step 2 is the real check"; "create a session"; "2:1:1 profile" | Step 2 runs `turns.sh`, not a bare curl. The reader never creates a session by hand. "2:1:1 profile" is a compressed label. | Name `turns.sh`, drop "create a session", and write "two model calls and one tool call per turn". | still real |

### tutorial/part-2/2.4-your-own-server.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 13–14 | "the metrics are recorded but never leave the process" | With no `MeterProvider` installed, OpenTelemetry records nothing at all. | "…nothing installs a `MeterProvider`, so the metrics are never recorded." | still real |
| 150–160 | "`get_gcp_exporters` builds the resource by merging two detectors" | `get_gcp_exporters` builds exporters only (`adk/telemetry/google_cloud.py:80-148`). The resource merge happens in `get_gcp_resource` (`:335-352`), which only the CLI calls (`adk/cli/api_server.py:712`). | Attribute the merge to `get_gcp_resource`, and say only the CLI calls it. | still real |
| 37 | `#why-the-script-needs-gcpprojectid` | The link goes nowhere; the heading's real anchor is `#why-the-script-needs-gcpproject_id`. | Fix the anchor. Better, retitle the heading as a question, "Why does a script need `gcp.project_id`?", and link to that. | still real |

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| `examples/03_metrics_server.py`, around lines 72–75 | The comment "else fall back" | The code has no fallback, so the comment describes behavior that doesn't exist. | Remove the comment. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 23–29, 39–48 | The snippet `maybe_set_otel_providers([hooks])`, and Step 1's `export OTEL_RESOURCE_ATTRIBUTES=…,gcp.project_id=…` | The script really passes `otel_resource=Resource.create({"gcp.project_id": …})`, so the snippet doesn't match the code, and the export is unnecessary. | Show the call the script makes, and remove the export. | still real |
| 94–95, 119–122 | "`job="adk-metrics"` … so only your own server appears" | Page 2.1's `adk web` used the same service name, instance and location, so both servers write to the same series. In the rerun they merged into one series, and the counter reset when the server restarted. | Give this server a distinct `OTEL_SERVICE_NAME`, or tell the reader to stop page 2.1's server and query a time window after it stopped. | still real |
| 119 | "exports the same six metrics as `adk web`" | The names match, but here the two `client.*` metrics carry ADK's labels and scope instead of the genai instrumentation's. | Say that the names match but the `client.*` labels differ. | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 59–66 | A curl loop timed with `date +%s.%N` | `%N` (nanoseconds) works only in the GNU version of `date`; on macOS it prints a literal "N". | Use `curl -w '%{http_code} %{time_total}s\n'`, or add a `/chat` mode to `turns.sh`. | still real |
| 32–34 | "every `OTEL_*` variable can live in `.env` here" | A variable already exported in the shell takes precedence over `.env`, which surprises readers. | Add: "If the variable is already exported in your shell, the shell value wins." | still real |
| 18, 152 | A reference to the logging tutorial with no link; "Agent Engine" | The reader can't follow the reference. The tutorial calls the product "Agent Runtime" everywhere else. | Add the link, and write "Agent Runtime" in prose. | still real |

### tutorial/part-2/2.5-agent-runtime.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 67, 72–74, 102 | Line 67: "Note the reasoning-engine id … the next step needs it". Lines 72–74: "you never copy the reasoning-engine id". Line 102: "paste the id Step 4 printed" | The three lines contradict each other about whether the reader copies the id. | Pick one flow: delete line 67, and have Step 4 `export ENGINE_ID` from its own output. | still real |
| 128 | "`instance` is a runtime-supplied id" | ADK generates the id itself, as `{uuid4().hex}-{pid}` (`adk/telemetry/google_cloud.py:317`). | "`instance` is an id ADK generates for each process" | still real |
| 181 | "(`google/adk/telemetry/google_cloud.py:244`)" | The code is elsewhere. | `adk/telemetry/_agent_engine.py:241`, called from `adk/telemetry/google_cloud.py:253` | still real |

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| whole page | 919 words; Step 6 teaches a second lesson | House style caps pages at 750 words and one lesson each. Step 6 (Agent Runtime's own service metrics) is a separate topic. | Move Step 6 to a deep dive. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 186–190 | "the points leave as the turns complete, not on a clock" | The exporter waits at least 5 seconds between exports (`_agent_engine_metric_exporter.py:162-190, 313-323`). Points recorded in the last 5 seconds before the run ends are never sent. The rerun exported 9 of 10 turns. | Describe the 5-second minimum and the lost last turn. Fix the docstring in `load/ae_turns.py` (lines 8–10), which makes the same claim. | still real |
| 144–153 | `request_count` "tracks your turns", with value `12` and labels `reasoning_engine_id` and `location` | The rerun read 20, because the metric also counts `create_session` calls. The metric took about 8 minutes to appear, and it carried the labels `response_code` and `response_code_class`. | Recapture from one run, and tell the reader to expect a delay of several minutes. | still real |
| 177 | "Every other route installs a `PeriodicExportingMetricReader` that flushes on a 5 s daemon thread" | The OTLP route configured through environment variables exports every 60 seconds, not 5. | "Every other Google route…" | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 35–49 | Step 2 has no command | It's labeled as a step, but the reader has nothing to do; it explains how the demo agent already handles the model's region. | Remove the step label. Give the explanation one sentence in the page body and move the detail to a deep dive. | still real |
| 22–79 | `$PROJECT_ID` and `$REGION` used without `source env.sh`; Step 3 has no expected output or time estimate | A reader in a new shell lacks the variables. A deploy that runs for minutes with no expected output looks stuck. | Add `source env.sh`, show the line that means the deploy finished, and say "takes several minutes". | still real |

### tutorial/part-2/2.6-other-backends.md

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 19–20 | "You do not touch the flag or the code, only the endpoint variables." | The reader does change the flag: `--otel_to_cloud` must be removed (or, in code, the Google Cloud hooks), or both routes run. | "Drop `--otel_to_cloud` (or the Google Cloud hooks in code) and set the endpoint variables." | still real |
| 36 | "Two limits carry over from the Google path" | The two limits are not inherited from the Google path; they belong to the OTLP exporter. | "Two limits apply:" | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 24–46 | Claims about exporter behavior with no source | The reader can't check them. The fact checker confirmed both claims. | Cite `adk/telemetry/setup.py:124-147` (the OTLP exporter) and `:156-159` (only the http/protobuf protocol is supported). | still real |
| 59–74 | "SigNoz, as one documented example", with no link; a code block nobody ran | The reader can't find the docs, and the block looks like captured output. The rerun skipped it because no backend endpoint was available. | Link the SigNoz docs, and label the block illustrative. | still real |

### tutorial/part-3/index.md

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 7, and every Part 3 nav line and subtitle | "Consume — signals from histograms" | House style uses em dashes only in step labels. Part 2's nav already writes this title with a colon. | "Consume: signals from histograms" | still real |
| 11–23 | The "Why you are here" note runs three sentences, followed by a 100-word paragraph | House style keeps the note to two sentences and the landing page short. | Cut to two sentences and one short paragraph. | still real |

### Findings that apply to every Part 3 page

**Wrong**

| Where | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 3.1 line 86; 3.2 line 46; 3.3 line 50; 3.4 line 49; 3.5 lines 44 and 76; 3.6 lines 30, 63 and 88; 3.7 line 72 | `export PROJECT=jwd-gcp-demos` | Every query runs against the author's project, not the reader's. The reader either gets a permission error or reads someone else's data. | `export PROJECT=$PROJECT_ID`, after `source env.sh` | still real |

**Style**

| Where | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 3.2, 3.3, 3.4, 3.7 | Each query appears twice: once in its own code block, once inside `export QUERY=` | Showing the same text twice makes the reader compare them for differences. | Show each query once, inside the export. | still real |

**Unclear**

| Where | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 3.2 to 3.7 | The pages never say the server started on page 3.1 must still be running | A reader who stopped it gets no new data and no explanation. | Add "Keep the page 3.1 server running." On page 3.7, where the server restarts: "Stop it with Ctrl+C, then:" | still real |

### tutorial/part-3/3.1-latency-three-grains.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 112–118, 139–143 | "the model holds at 4.83 s" | See top finding 5. The model-call histogram uses the default bucket boundaries of 0, 5, 10, 25 seconds and up (visible in `out/metrics.json`; the OpenTelemetry semantic-conventions code sets no custom boundaries). When every call is under 5 seconds, the 95th percentile is just a point interpolated inside the first bucket, about 4.75, and means only "every call took under 5 seconds". The rerun gave exactly 4.75. | Drop the model-call 95th percentile. Or configure finer buckets for the model-call histogram with an OpenTelemetry view, and show that. | still real |
| 53–61 | `slow-tool turn 1 http=200 0.51s` … `turn 2 2.18s` | Presented as captured output, but real turns take 3 to 6 seconds. | Replace with lines captured from a real run. | still real |
| 155–167 | The deep dive's output `get_forecast p95 2.09s` | No command on the page prints this line. The rerun's 95th-percentile turn latency under concurrent load was 11.86 seconds, not the page's "about 7.7". | Show the three curl commands and the output they really produce. | still real |
| 179–180 | `</content>` and `</invoke>` at the end of the file | Leftover tool-call markup from drafting, rendered as text. | Delete both lines. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 139–143 | "The turn slows while the model stays flat and one tool owns the rise" | "Slows" and "stays flat" need a comparison, but the page takes one reading with no baseline. The rerun gave turn 6.19 seconds, model 4.75 seconds and tool 2.24 seconds, so the model, not the tool, takes most of the time. | Run the `baseline` scenario first, then `slow-tool`, and compare the two. | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 133 | A `get_forecast` 95th percentile of `2.163` seconds, when the tool sleeps only 0.3 to 1.5 seconds | The reader can't see how the value exceeds the longest sleep. It's interpolated inside the 1.28 to 2.56 second bucket. | Explain that the percentile is interpolated within a bucket, so it can exceed any real value. | still real |
| 12–15, 64–81 | The "Why you are here" note names no scenario; Step 3 has no Command label or expected output; "ADC bearer token" | The page doesn't say which scenario it runs. Step 3 leaves the reader unsure what to run and what to expect. "ADC" is never defined. | Name the `slow-tool` scenario in the note, add the labels to Step 3, and spell out Application Default Credentials (ADC) on first use. | still real: Step 3 is now a browser step; the note and "ADC" remain |

### tutorial/part-3/3.2-volume-and-shape.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 60–80 | `sum by (le) ({"gen_ai.invoke_agent.tool_calls_bucket"})`, which the page says shows "a spike near le=1 … and a second near le=3" | Histogram buckets in PromQL are cumulative: each bucket counts every turn at or below its boundary, since the server started. The query can't show two separate spikes. The rerun returned 5 turns at or below 0 tool calls, 80 at or below 1, and 90 at or below 3. | Use `sum by (le) (increase({…_bucket}[15m]))`, and subtract each bucket from the next to get the count in each range. | still real |
| 38–58 | "Divide the sum … by their count", but the command shown computes only turns per minute | The page describes a calculation it doesn't perform. | Add the two mean-per-turn queries from `queries/volume.promql`. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 17–19, 83–87 | "those turns make more model and tool calls"; "mean above the baseline 2 and 1"; "Repeated work, not a slow dependency, is driving the cost" | The rerun gave 1.91 model calls per turn (below the baseline of 2) and 1.23 tool calls. Three-city turns add tool calls, not model calls, and 5 of 90 turns didn't call the tool at all. | Claim only that tool calls per turn rise. | still real |

### tutorial/part-3/3.3-errors.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 70–84 | The invocation error ratio "reads 0" | With no errors, the numerator has no series, so the query returns no data (`"result":[]`), not 0. | Use `(sum(rate({…, "error.type"=~".+"}[5m])) or vector(0)) / sum(rate({…}[5m]))`, which returns 0. Or say "returns no data, which here means zero". | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 19 | "(1.3)" | A bare page number, not a link. | Link to page 1.3, and cite `demo_agent/agent.py:100-103`. | still real |

The tool error ratio matched the page: the rerun gave exactly 0.5.

### tutorial/part-3/3.4-tokens-and-cost.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 63–80 | "stepped across the run to see input per call rise", run against `/api/v1/query` | `/api/v1/query` is an instant query and returns one number (the rerun got 1513), so the reader can't see anything rise. A range query can. In the rerun, `query_range` with a 15-second step showed input tokens per call rising from 357 to 1570 while output stayed flat at 14 to 16. | Give the `/api/v1/query_range` command with a 15-second step, and show that output. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 95–126 | The deep dive about instrumentation scope says the client metrics come from the genai scope | That's only true for a Gemini agent with the genai instrumentation active (`adk/telemetry/tracing.py:993-1001`). The deep dive also shows a `count by` value of 2 without saying it counts series, not calls. | Add "for a Gemini agent with the genai instrumentation active", and explain that the 2 is the number of series. | still real |

### tutorial/part-3/3.5-a-dashboard.md and queries/dashboard.json

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| Step 2 | `gcloud monitoring dashboards create --config-from-file=queries/dashboard.json` | Fails with `Unknown name "//"`: the JSON uses `//` as a key to hold comments, and the API rejects unknown keys. | Remove the five `//` keys from the JSON. | still real |
| `dashboard.json` line 72 | `otel_scope_name=\"gcp.vertex.agent\"` on the tokens-per-minute widget | Token metrics carry the genai scope, not `gcp.vertex.agent`, so this widget shows nothing. It was the only empty query of the nine. | Remove the scope filter. | still real |
| 17–19, 58–59, 67 | "four widgets"; "the same six histograms" | The JSON has 8 widgets, which read 4 histograms. | "eight widgets reading four histograms" | still real |
| 53 | `Created [projects/jwd-gcp-demos/dashboards/...]` | gcloud prints only the bare id, for example `Created [28196eb4-…]`. | Show the real line. | still real |
| 77 | `export DASHBOARD_ID=NEEDS-RUN` | A placeholder the reader can't fill in; the cleanup command fails. | Capture the id in Step 2 by adding `--format='value(name)'` to the create command. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 21, 62–64 | Scenario `baseline`; "Confirm every widget renders data" | The `baseline` scenario produces no errors, so the error-ratio widget has no data. The reader will think it's broken. | Run `unknown-city` instead, or say the error-ratio widget stays empty under `baseline`. | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 20, 62–68 | "mirrors a well-known ADK dashboard"; Step 3 written as a paragraph, with a console code block standing in for a browser view | The reader can't tell which dashboard is meant. A code block can't show what a browser page looks like. | Name and link the dashboard, or cut the sentence. Use bullets for Step 3, and describe in words what the reader should see. | still real |

### tutorial/part-3/3.6-an-alert.md and queries/alert-policy.json

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| Step 1 | `gcloud alpha monitoring policies create --policy-from-file=queries/alert-policy.json` | Fails on the `//` comment keys, as in page 3.5. With them removed, the generally available `gcloud monitoring policies create` works, so `alpha` isn't needed. | Remove the `//` keys, and drop `alpha`. | still real |
| 57–73 | "Read the open incidents" using `policies list` | `policies list` lists alert policies, not incidents. | Use `GET /v3/projects/$PROJECT/alerts?filter=state="OPEN"` (the rerun returned an incident with value 0.493), or the console path **Monitoring → Alerting → Incidents**. | still real |
| 89 | `export POLICY_ID=NEEDS-RUN` | A placeholder the reader can't fill in; the cleanup command fails. | Capture the id when the policy is created. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 42–48 | `load/turns.sh unknown-city 120`, with no timing | The load took 8.5 minutes. The incident opened about 10 minutes after the policy was created, 2 minutes after the load ended. A reader who checks early sees nothing and assumes failure. | Tell the reader how long to wait. | still real |
| 13–15, 76–80 | "pages when it breaches"; "every user got an answer" | The policy has no notification channel, so it only opens an incident; it pages nobody. The Atlantis users got no weather (pages 3.3 and 3.7 say so). | Remove "pages", and replace the second claim with: "It fires on any failing dependency, including turns the agent recovers from." | still real |

### tutorial/part-3/3.7-task-outcome.md and queries/outcome.promql

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 64, 66, 74, 84 | `{"tutorial.weather.requests_total"}` | The metric is stored as `…/tutorial.weather.requests/counter`, with no `_total` suffix, so the query returns nothing. | Use `{"tutorial.weather.requests"}` (the rerun gave 0.5). Fix `queries/outcome.promql` too. | fixed on main |

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 94–98 | A warning hidden in a NOTE callout; "Missing is not zero" | A trap belongs in a deep dive with a question heading. "Missing is not zero" is a slogan that only makes sense once you know the point. | Move it to a deep dive with a question heading, spell out what "missing" means, and run the coverage query (the rerun gave 1). | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 18–24, 87–92 | The counter "closes the gap"; "This is the counter to alert on" | The counter reads the tool's `status` field, so under `unknown-city` it equals page 3.3's tool error ratio, and the page shows nothing new. It also counts per tool call, not per task (`outcome.py:64-67`). | Choose a scenario where the counter and the tool error ratio give different answers. Otherwise, describe the counter as an approximation of task outcome. | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 40–44 | `adk web --otel_to_cloud` with no `source env.sh` and no step to stop the earlier server | The reader may lack variables, or hit a port conflict with page 3.1's server. | Add `source env.sh` and a stop step, and `unset TUTORIAL_OUTCOME_METRIC` at the end so later pages see six metrics again. | still real |
| 31–34 | The gate `os.getenv("TUTORIAL_OUTCOME_METRIC")` | Any non-empty value turns the metric on, including `0`, which a reader would expect to turn it off. | Say "any non-empty value turns it on", or change the code to compare against `"1"`. | still real |

### tutorial/part-4/index.md

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 7, and every Part 4 nav line and subtitle | "Consume — rows in BigQuery" | Same em-dash issue as Part 3. | "Consume: rows in BigQuery" | still real |
| 21–34 | No link to the Scenarios page | This tutorial's convention is that every part landing page links to Scenarios. | Add the link. | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 17 | "traded detail for cheapness" | Compressed: the reader has to infer what detail and whose cheapness. | "gave up per-event detail to keep storage cheap" | still real |

### Findings that apply to pages 4.1 to 4.4

**Wrong**

| Where | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 4.1 lines 53–62; 4.2 line 24; 4.3 line 25; 4.4 line 23 | `.venv/bin/python examples/04_bq_plugin.py`, then `load/turns.sh baseline 10` | The two don't fit together. `04_bq_plugin.py` serves only `POST /chat` on port 8080, with a fixed `user_id="u1"` and a new session per call. `turns.sh` sends requests to `/apps/…/sessions` and `/run` on port 8000. Every turn returned 404, and the script still printed "good to go". | Attach the plugin to `adk api_server` instead, or add those routes to `04_bq_plugin.py`. Then have the page export `HOST` so `turns.sh` finds the server. | fixed on main |
| Queries on 4.2, 4.3 and 4.4 | Queries over the whole `agent_events` table | Rows from earlier pages stay in the table and skew every later result. Page 4.2's growing-context session ranked first on page 4.3, and the page 4.4 evaluator scored 42 sessions. | Filter each query by `session_id` or `timestamp`, or give each page its own dataset. | still real: 4.2 and 4.3 now explain the mix, but 4.2's query still reads the whole table |

**Unclear**

| Where | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 4.1 lines 31 and 56, and 4.2 to 4.6 | `BQ_ANALYTICS_DATASET_ID` exported in one shell; a "second shell" opened later | The second shell doesn't have the variable, so commands there use the wrong dataset or fail. | "In each shell, run `source env.sh` and `export BQ_ANALYTICS_DATASET_ID=agent_analytics`." | still real: Part 4's second shell now exports it, but Step 1 runs `bq mk` without `source env.sh` |

### tutorial/part-4/4.1-one-line-one-table.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 102 | `SELECT event_type, COUNT(*) AS rows` | Fails with `Syntax error: Unexpected keyword ROWS`, because `ROWS` is reserved in BigQuery. | Use `AS n`. For the expected output: the rerun counted 12 rows per turn, with 20 each of LLM_REQUEST and LLM_RESPONSE and 10 each of 8 other event types over 10 turns. | fixed on main |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 72–74, 89–90 | "one `v_<event_type>` view per event type it has seen" | The plugin creates all 25 views at startup, whether or not that event type has occurred (`adk/plugins/bigquery_agent_analytics_plugin.py:5094-5113`). | "one `v_<event_type>` view for each of the 25 event types, created at startup" | fixed on main |
| 114–125 | "`trace_id`, `span_id` \| The Cloud Trace join keys" | `span_id` is the plugin's own internal id, not an OpenTelemetry span id (`bigquery_agent_analytics_plugin.py:3647-3659`). `trace_id` matches Cloud Trace only when a trace is active, and `04_bq_plugin.py` sets up no tracing. | Explain that neither column joins to Cloud Trace in this demo. | fixed on main |
| 148–149 | "jobUser … lets it run the query and metadata jobs that create the table and views" | The two roles do different things. `jobUser` runs the `CREATE VIEW` jobs; `dataEditor` creates the table and writes the rows. | Describe each role separately. | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 18–19 | "Grant those to your ADC identity before you start." | The reader isn't told how to grant the roles, or whether they already have them. | Give the `add-iam-policy-binding` commands, or note that a project Owner already has both roles. | still real |
| 46–48 | "batches with `batch_size=1` and flushes on each run end" | Describes configuration, not what the reader will see. | "By default, the plugin writes each event within about a second." (The rerun could query rows within about 3 seconds.) | still real |

### tutorial/part-4/4.2-tokens-latency-cache-per-call.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 72–97 | "should match the histogram `sum`"; "Two stores, one truth" | Input tokens matched exactly (23,530 in both). Output tokens didn't: 637 in the rows versus 1,881 in the metrics, because the histogram includes thinking tokens and the rows report them separately. | Sum `usage_completion_tokens + usage_thinking_tokens` on the row side, and use `increase(…[30m])` on the metric side. | fixed on main |
| 106–109 | "`v_tool_completed` … with its `latency_ms`"; "`v_tool_error` has one row per tool that returned an error status" | The column is named `total_ms`. `v_tool_error` gets rows only when a tool raises an exception; it had 0 rows after 5 Atlantis errors. | Use `total_ms`, and explain that returned error statuses don't reach `v_tool_error`. | still real |
| 67 | "`usage_thinking_tokens` \| Reasoning tokens, inside completion" | Thinking tokens are reported separately, not included in the completion count. | "reported separately from `usage_completion_tokens`" | fixed on main |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 41–58 | `ORDER BY usage_total_tokens DESC`; cache columns described as "non-zero" | Sorting by size reverses the climb the page wants to show. The cache columns were NULL on all 42 rows. | Use `WHERE session_id = … ORDER BY timestamp`, and tell the reader to expect no cache hits. The rerun saw prompt tokens rise from 323 to 1151. | still real: cache NULLs are now explained; the size ordering remains |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 57 | `ttft_ms` among the columns shown | Time to first token equals `total_ms` on every row, because the demo doesn't stream. | Say so, or drop the column. | still real |

### tutorial/part-4/4.3-cost-per-session-and-user.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 70 | `JSON_VALUE(content, '\$.text') AS prompt` | NULL on every row, because the field is named `text_summary`. | Use `'\$.text_summary'`. | fixed on main |
| 60–71 | "join back to the user message for the top invocation" | The query doesn't join anything; it lists the 5 most recent messages. | Filter by the `invocation_id` found in Step 1. | fixed on main |

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 84–87 | The WARNING runs three sentences | House style keeps a WARNING to one sentence. | Cut to one sentence. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 18–20, 55–58 | "three-city sessions rank above"; "three times the work" | Rank 1 was page 4.2's session, not a three-city one. Three-city turns made 3 tool calls but used only about 14% more tokens (941 versus 829). | Filter out earlier pages' sessions, and replace "three times the work" with the measured difference. | still real: the ranking is now explained; "three times the work" remains |
| title, 36 | "per user" | Every session has the same user, `load-user`, so there's nothing to compare across users. | Drop "per user", or have the load vary `USER_ID`. | still real |

### tutorial/part-4/4.4-the-sdk.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 51–59 | `export BQ_TRACE_ID=<invocation id …>` | Fails with `ValueError: No events found for trace_id=e-…`. `get_trace()` takes a trace id (32 hex characters), not an invocation id. | Select the `trace_id` column instead, or use `get_session_trace(session_id)`. | fixed on main |
| 83–85 | `--project` and `--dataset` | Fails with `No such option: --project`. | Use `--project-id` and `--dataset-id`, and add the required `--evaluator`. | fixed on main |
| 76–78, 91–98 | "summarizes the whole table … tool error rate near 0.5" | The command runs one evaluator per call and reports a pass rate per session, not a summary of the table. Its `error_rate` counts only raised exceptions, so the rerun saw 0.0 (see top finding 7). | Show the 0.5 rate with SQL on `v_tool_completed`, filtering on `JSON_VALUE(tool_result,'$.status')='error'`. | fixed on main |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 65–70 | "The failing tool call and the model's recovery are both visible" | `render()` shows the call as `[✓] TOOL_COMPLETED … (get_weather)`, with a success mark. The error is visible only inside the `content` field. | Say the error shows only in `content`, and point to it. | fixed on main |
| 107–110 | "The subcommands read only" | Some subcommands write, including `views` and `evalbench-import`. | Name which subcommands write. | fixed on main |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 32–47 | `pip install bigquery-agent-analytics` | The package is already in `requirements.txt`, so the reader installed it during Setup. | Replace the install with "confirm it is installed with `pip show bigquery-agent-analytics`". | still real |

### tutorial/part-4/4.5-looker-studio-template.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 22–34 | The flow "Make a copy", choose BigQuery, pick the table | The template doesn't work this way. Its README uses a configurator that builds a Looker Studio Linking API URL. | Link the README (`GoogleCloudPlatform/BigQuery-Agent-Analytics-SDK/dashboard/looker_studio/README.md`) and give its steps as bullets. | still real |
| 38–46 | A table describing four groups of charts | The template has 8 pages, including a Trace Inspector. | Describe the template's real pages. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 54–57 | The TIP says a viewer "sees the charts without direct access to the `content` column" | With the owner's credentials, viewers see whatever the charts show, and the Trace Inspector page can display content. | Qualify the TIP to say what viewers can see. | still real |

**Unclear**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 12–16 | No scenario or question; no step to delete the copy | The reader doesn't know what the page answers, and the copy breaks once page 4.6 deletes the dataset. | Add the scenario and question, and "Delete your copy afterward; it stops working once page 4.6 deletes the dataset." | still real |

The page's "37 charts" claim is correct.

### tutorial/part-4/4.6-metrics-or-rows.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 19, 24 | "About a minute (batched write)" | Rows arrive in about a second (`batch_flush_interval=1.0`); the rerun saw them within about 3 seconds. Page 4.1 says the same. | "About a second" | fixed on main |
| 36 | The diagram edge `M -. "trace_id (opt-in)" .-> T` | The diagram shows metrics linked to traces by a trace id, but metrics carry no trace id. | Delete the edge. | fixed on main |
| 44–50 | "set `enable_otel_correlation=True` … each row is stamped with the ambient trace and span ids" | `trace_id` is set on every row regardless. The flag adds two extra attributes, `attributes.otel.span_id` and `attributes.otel.trace_id` (`bigquery_agent_analytics_plugin.py:6195-6210`). Joining to Cloud Trace also needs an app that exports traces, and `04_bq_plugin.py` doesn't. | Describe what the flag really adds, and say the join needs trace export turned on. | fixed on main |
| 60–64 | `bq rm --recursive --dataset …` | The command asks for y/N confirmation. Run without a person to answer, it exits without deleting anything. | Add `-f`, and stop the server before deleting the dataset. | fixed on main |

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 22–50 | Reference material, and a heading phrased as a statement, inside a hands-on page | House style keeps one lesson per page and phrases deep-dive headings as questions. The comparison is reference material. | Move the comparison to how-to-choose. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 26–30 | The comparison rows "Per series stored", "Weeks, then downsampled", and join key `span_id` | No source is given, and the first is wrong: Cloud Monitoring bills per sample ingested, not per series stored. | Cite the docs for each row, or remove the rows. | still real |

### tutorial/how-to-choose.md

**Wrong**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 18 | "the seven ADK emits (six for a single agent…)" | ADK emits six; the seventh needs the `Workflow` primitive. | "ADK emits six for a single agent. A seventh needs the `Workflow` primitive." | still real |
| 68–71, 85–98 | "Parts 1 … is verified … Parts 2 through 4 are drafted", and the "Not verified" table | Out of date: Part 2 and page 3.1 already have run records in `verification/`. | Move them to the Verified list, with dates. Add this review's results, including the failures on pages 3.5, 3.6, 3.7 and Part 4. | still real: partly updated; Part 2, 3.1, 3.4 and 3.7 still listed as unverified or pending |

**Style**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 59–64, 100–110 | "differs in two ways", where one of the two is not a difference; a reference list with no links | The first misleads the reader about how many differences there are. The second gives the reader nothing to click. | Rewrite the first, and add URLs to the reference list. | still real |

**Misleading**

| Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|
| 37, 50, 53–55 | `Client().get_trace().render()`; "the only join is a row's `trace_id` … enabled with `enable_otel_correlation=True`" | The call omits required arguments. The join description has the same error as page 4.6. | Use `Client(project, dataset).get_trace(trace_id).render()`, and fix the join text as on page 4.6. | still real: the join text is fixed; `Client().get_trace()` remains |

---

## Demo runs

"Same structure" means the output had the same shape the page shows (the same metric names, labels and kinds of values), with numbers that differ because a live model was used.

| Page | Project | What was run | Result |
|---|---|---|---|
| Setup | jwd-dev-1 | `.venv/bin/python examples/01_console_metrics.py` | Matches, except the resource block (see the Setup findings). |
| 1.1 | jwd-dev-1 | `examples/01_console_metrics.py` | Matches: 6 metric names, and input tokens in the 250 to 500 bucket. |
| 1.2 | jwd-dev-1 | `examples/03_histogram_shape.py` | Same structure: 20 model calls, with buckets holding 1, 3, 15 and 1. |
| 1.3 | jwd-dev-1 | `examples/02_two_attribute_sets.py` | Matches. |
| 1.4 | jwd-dev-1 | `examples/01_console_metrics.py` with `ADK_EXPERIMENTAL_TELEMETRY=true`, then again with it unset | Matches: 12 metric names, then 6. `total_tokens` was 817, the sum of 717 input and 100 output. |
| 1.5 | jwd-dev-1 | `examples/05_workflow_metrics.py` | Matches, but no DeprecationWarning appears because the script silences it. |
| 2.1 | jwd-dev-2 | `adk web --port 8100 --otel_to_cloud ./`, `turns.sh baseline 20`, the PromQL query, and `plot_tokens.py` | Matches. |
| 2.1 deep dive | jwd-dev-2 | The export-outage experiment | Matches: six 400 errors, and the count stayed at 20. |
| 2.2 | jwd-dev-2 | Listing metric descriptors and their label keys | Differs: 6 descriptors, not 7, and the label table is wrong. |
| 2.3 | jwd-dev-2 | `adk deploy cloud_run`, `turns.sh baseline 20`, the PromQL query, and the cleanup | Same structure, peaking at about 8 model calls, 4 turns and 4 tool calls per minute. Cleanup leaves a container image and a source archive. |
| 2.4 | jwd-dev-2 | `PORT=8180 examples/03_metrics_server.py`, the curl loop, and the PromQL query | Same structure, with rates of 4, 1.56 and 4 per minute in the page's order (model calls, turns, tool calls). Two of the turns took about 50 seconds. This server's series merged with page 2.1's. |
| 2.5 | jwd-dev-2 | `adk deploy agent_engine`, `ae_turns.py`, the PromQL query, and `ae_delete.py` | Matches: 3.6 model calls, 1.8 turns and 1.8 tool calls per minute. Only 9 of 10 turns were exported. |
| 2.5 Step 6 | jwd-dev-2 | Reading `request_count` | Differs: no data for about 8 minutes, then 20, not 12. |
| 3.1 | jwd-dev-3 | `adk web --port 8230`, `turns.sh slow-tool 30`, and the three 95th-percentile queries | Differs: turns took 3 to 6 seconds. The 95th percentiles were 6.19 seconds (turn), 4.75 (model call) and 2.24 (tool call). |
| 3.1 deep dive | jwd-dev-3 | `turns.sh concurrent 20` | Differs: the 95th-percentile turn latency was 11.86 seconds. |
| 3.2 | jwd-dev-3 | `turns.sh multi-city 40` and the page's queries | Differs: 1.91 model calls per turn, and the bucket counts are cumulative. |
| 3.3 | jwd-dev-3 | `turns.sh unknown-city 40` and the two error ratios | The tool ratio matches at 0.5. The invocation ratio returns no data rather than 0. |
| 3.4 | jwd-dev-3 | `turns.sh growing-context 20` and the page's queries | Step 2 matches. Step 3 needs a range query (`query_range`) to show anything. |
| 3.5 | jwd-dev-3 | `turns.sh baseline 30`, then creating the dashboard | **Fails** on the `//` keys. With them removed, the dashboard is created, but the tokens widget is empty. |
| 3.6 | jwd-dev-3 | Creating the alert policy, `turns.sh unknown-city 120`, and reading the incident | **Fails** on the `//` keys. With them removed, an incident opened (value 0.493), but `policies list` can't show it. |
| 3.7 | jwd-dev-3 | `TUTORIAL_OUTCOME_METRIC=1`, `turns.sh unknown-city 40`, and the outcome query | **Fails**: the `_total` suffix returns nothing. Without the suffix, the query gives 0.5. |
| 4.1 | jwd-dev-4 | `bq mk`, `PORT=8380 examples/04_bq_plugin.py`, and `turns.sh baseline 10` | **Fails**: every turn returns 404. |
| 4.1 | jwd-dev-4 | `bq ls` and the event-type query | The list of views differs from the page. The query **fails** on the reserved word `rows`. |
| 4.2 | jwd-dev-4 | `turns.sh growing-context 10` (through a temporary adapter, see below) and the page's queries | The token climb matches. Cache columns are NULL. Output tokens don't reconcile with the metrics. |
| 4.3 | jwd-dev-4 | `turns.sh multi-city 20` (through the adapter) and the page's queries | The ranking is skewed by earlier pages' rows. The prompt query **fails** (every value is NULL). |
| 4.4 | jwd-dev-4 | `turns.sh unknown-city 10`, `render()`, and `evaluate` | **Fails** on the trace id and on `--project`. The error rate reads 0.0. |
| 4.6 | jwd-dev-4 | `bq rm --recursive --dataset` | Differs: unattended, it stops at the confirmation prompt. Answering `y` deletes the dataset. |

**Where the reruns departed from the pages:**
- Ports 8100, 8180, 8230 and 8380 replaced the defaults so the demos could run at the same time.
- Files the pages write to `out/` went to a scratch directory instead.
- Console views were checked by running the same queries through the API.
- Pages 4.2 to 4.4 used a temporary adapter in a scratch directory that added the `adk api_server` routes to the `04_bq_plugin.py` app, so `turns.sh` could run unchanged. Without it, those pages couldn't be tested at all (see the Part 4 findings).

### Skipped demos

| Demo | Reason |
|---|---|
| Setup: creating the virtual environment, `pip install`, `gcloud services enable`, and the credentials login | The existing virtual environment was reused, and the APIs were already enabled in the dev projects. |
| 2.5 Step 1: `pip install` | `pip install --dry-run` showed every package already installed. |
| 2.6: SigNoz and other OTLP backends | No backend endpoint was available. |
| 4.5: the Looker Studio template | It runs only in a browser. The template link was checked and resolves (it redirects to datastudio). |
| Metrics Explorer views on pages 2.1 to 2.5, 3.1 and 3.5 | They run only in a browser. The same PromQL queries were run through the API instead. |

No demo was skipped for cost. All runs together were estimated to cost under $3.

---

## Inconsistencies between pages

| # | Inconsistency | Pages | Status |
|---|---|---|---|
| 1 | When the seventh metric appears. Page 1.1 says it "stays silent until 1.5"; page 1.4 says it "can finally appear" on 1.5; page 1.5 says it still doesn't appear; page 2.2 says it is "present because 1.5 created it"; how-to-choose says "the seven ADK emits". | 1.1, 1.4, 1.5, 2.2, how-to-choose | still real |
| 2 | Whether Part 1 needs Google Cloud. Some pages say "no Google Cloud account", while Setup requires Vertex AI and credentials. | README, TUTORIAL, part-1/index, Setup | still real |
| 3 | The same datapoint is shown with 1 attribute on one page and 3 on another. The real datapoint has 6. | Setup, 1.1 | still real |
| 4 | Healthy tool latency: 0.002 seconds in page 1.1's capture, but 0.02 to 0.64 seconds in page 1.3's invented panels. | 1.1, 1.3 | still real |
| 5 | The instrumentation scope label. Page 2.2 says every descriptor has `gcp.vertex.agent`; page 3.4 says the client metrics have the genai scope; page 3.5's dashboard filters on `gcp.vertex.agent`. | 2.2, 3.4, 3.5 | still real |
| 6 | The project variable. Setup and Part 2 use `PROJECT_ID`; Part 3 hardcodes `PROJECT=jwd-gcp-demos`. | Part 2, Part 3 | still real |
| 7 | What happened to Atlantis users. Pages 3.3 and 3.7 say they got no weather; page 3.6 says "every user got an answer". | 3.3, 3.6, 3.7 | still real |
| 8 | How soon BigQuery rows appear: "about a second" on page 4.1, "about a minute" on page 4.6. | 4.1, 4.6 | fixed on main |
| 9 | Whether metrics link to Cloud Trace. Page 4.6's text says metrics carry no trace id; its diagram and how-to-choose draw a link. | 4.6, how-to-choose | fixed on main |
| 10 | What `out/metrics.json` holds. In Part 1 it is the metric reader's output; page 2.1 overwrites it with a PromQL response. | Part 1, 2.1 | still real |
| 11 | Shell date commands that work on only one platform. Pages 2.1 and 2.2 use the macOS-only `-v-30M`; page 2.4 uses the Linux-only `%N`. | 2.1, 2.2, 2.4 | still real |
| 12 | Three names for one product: Agent Runtime, Agent Engine and reasoning engine. | 2.4, 2.5 | still real |
| 13 | The part-title separator: a colon in page 2.6's nav line ("Consume: …"), an em dash in Parts 3 and 4 ("Consume — …"). | 2.6, Part 3, Part 4 | still real |
| 14 | The "Why you are here" notes. Almost none name a scenario and an operational question, and most run to three sentences instead of two. | All lesson pages | still real |
| 15 | Two pages exceed the 750-word limit: 2.1 (923 words) and 2.5 (919 words). | 2.1, 2.5 | still real |

---

## Leftovers

**Cloud resources this review created:** all deleted.

| Project | Created | Deleted |
|---|---|---|
| jwd-dev-2 | Cloud Run service `adk-metrics-otel`, its Artifact Registry image and source archive, and Agent Engine instance `7194447078410420224` | Yes |
| jwd-dev-3 | One dashboard and one alert policy | Yes |
| jwd-dev-4 | BigQuery dataset `agent_analytics` | Yes |

**Resources in jwd-dev-2 that this review did not create, left in place:**
- Cloud Run services `adk-trace` and `my-agent`
- reasoning engine `3745815663751462912`
- the shared bucket `gs://run-sources-jwd-dev-2-us-central1`
- the Artifact Registry repository `cloud-run-source-deploy`

**jwd-gcp-demos:** nothing was written. The Part 4 demo ran three read-only `bq query` SELECT statements that billed jwd-gcp-demos, against tables in `jwd-dev-4`.

**Untracked files reported by `git status --porcelain`:**

| When | Untracked files |
|---|---|
| Before the demos | `docs/adk-metrics-style-review.md` |
| After the demos | `docs/adk-metrics-style-review.md`, `docs/adk-tracing-review-2026-10-02.md` |

The tracing review file came from a separate session reviewing the tracing tutorial at the same time, not from this review. Temporary files from other sessions (`ai/adk/logging/Dockerfile`, `ai/adk/tracing/demo_agent_tmp…`) appeared and disappeared during the run.

---

## Appendix: the standards this review applied

The standards come from five sources, listed here in the order they win when two disagree:

1. **The tutorial-review skill:** `.claude/skills/tutorial-review/SKILL.md`. *Status: fixed on main (the server has the session and `/run` routes); still real: `turns.sh` prints "good to go" after failed turns.*
2. **This tutorial's conventions:** `ai/adk/metrics/CLAUDE.md`. *Status: still real.*
3. **The house tutorial style:** `.claude/skills/tutorial-style/SKILL.md` and the reference files in that folder. *Status: fixed on main.*
4. **Jeff's global writing rules** (the Writing section of `~/.claude/CLAUDE.md`), and Jeff's tutorial pedagogy note (`feedback-tutorial-pedagogy.md` in the project memory). *Status: still real.*
5. **The "set the env you read" note** in the project memory, which the review skill's own rule on exporting variables also covers. *Status: still real.*

**Where sources disagreed:**

| Topic | Standard applied | Standard overridden |
|---|---|---|
| Em dashes | House tutorial style: em dashes only in step labels. | Global writing rules, which allow one or two per large chunk of text. |
| Expected output | This tutorial's conventions: every console block must be captured from a real run. | House tutorial style and the pedagogy note, which treat captured output as a strong preference. |

### Standards this review found broken

| Standard | Source | Pages where it was broken |
|---|---|---|
| Write concisely, clearly and correctly. | Review skill; global writing rules | Throughout |
| Avoid shorthand: no compressed labels, metaphors or jargon that only make sense if you already know the point. | Review skill | Setup, Scenarios, 2.1, 2.3, Part 3, Part 4 |
| Use tables and lists where they fit, and keep tables well formed. | Global writing rules; house style | 2.2 |
| Use em dashes only in step labels. | House style | Part 3 and Part 4 titles, 2.1, 2.2 |
| Use one term for each concept. | House style | 1.1, 2.4, 2.5 |
| Cite the source file and line when the output doesn't show a claim. | House style | 1.3, 1.4, 1.5, 2.5, 2.6, Part 3 |
| Cut filler. | House style; global writing rules | TUTORIAL, 1.2, 2.1, 3.6, 3.7 |
| Teach one lesson per page. | House style | 2.5, 4.6 |
| Show only the code the lesson needs. | House style; pedagogy note | Setup, 2.4, 4.4 |
| Show only output captured from a real run. | This tutorial's conventions | 1.3, 2.3, 2.5, 3.1 to 3.7, 4.1 to 4.6 |
| Use real output to correct likely misconceptions. | House style | 1.2, 3.1, 3.2, 3.7 |
| Name a scenario and an operational question in every "Why you are here" note. | This tutorial's conventions | Nearly every lesson page |
| Stay consistent with the tutorial's central idea: a metric is recorded at one of three moments (a model call ends, a tool call ends, an agent invocation ends). | This tutorial's conventions | Setup, 1.3, 1.4 |
| Give each page a nav block whose links follow the reading order. | House style | part-1/index, 3.1 |
| Keep the "Why you are here" note to two sentences, and keep sections in the standard order. | House style | Most pages |
| Keep each page between 200 and 750 words. | House style | 2.1, 2.5 |
| Structure each step with a label, a command and expected output. | House style | 1.4, 2.5, 3.1, 3.5, 4.2 |
| Label blocks **Command:** and **Expected output**. | House style | Setup, 1.1, 1.4, 1.5, 2.1, 2.6, 3.1 |
| Show a request body or query once. | House style | Setup and 1.3, Part 3 queries |
| Write console directions as bullets, one action each. | House style; this tutorial's conventions | 2.1, 2.2, 3.5, 4.5 |
| Phrase deep-dive headings as questions, summarize each in the body with a link, and put gotchas there. | House style | Part 1, 2.1, 2.3, 2.4, 3.7, 4.6 |
| Give each part landing page the standard form and a link to Scenarios. | House style; this tutorial's conventions | Part 2, 3 and 4 landing pages |
| On the reference page, record what was verified and keep a "Not verified" table current. | House style | how-to-choose, 2.6 |
| Use each callout type for its purpose, at its standard length. | House style | 1.2, 1.4, 3.7, 4.3 |
| Make sure links exist and resolve. | House style; this tutorial's conventions | 2.1, 2.2, 2.4, 4.5 |
| Any step that reads an environment variable must export it first. | Set-the-env-you-read note; review skill | Part 3 project, 2.1 date command, 2.3, 2.5, Part 4 |
| A single agent emits six metrics; the seventh needs the `Workflow` primitive. | This tutorial's conventions | 1.1, 1.4, 2.2, how-to-choose |
| Query dotted histograms in PromQL with the quoted brace form and the right suffixes. | This tutorial's conventions | 3.7 |

### Full list of standards

**How the review was conducted** (all from the review skill)

- Treat tracked files as read-only.
- Don't edit `env.sh` or `.env`.
- Rerun every demo, unattended.
- Give each demo its own dev project, and never use jwd-gcp-demos.
- Export the project variables explicitly in the shell that runs each demo.
- Delete every cloud resource the review creates.
- Skip any demo likely to cost more than $2.
- Check facts against the pinned SDK version first, then the docs.
- Give each finding a severity tag, the quoted text, the standard it breaks, and a rewrite.

**Writing**

- Write concisely, clearly, cleanly, correctly and elegantly. (Review skill; global writing rules)
- Treat shorthand as a defect. (Review skill)
- Put the answer first, with no empty openers, closing summaries or hedges. (Global writing rules)
- Use tables and lists where they fit. (Global writing rules; house style)
- Don't describe your own words as honest, candid or frank. (Global writing rules)
- Use em dashes only in step labels. (House style, over global writing rules)
- Write in the second person and the imperative, with one term per concept. (House style)
- Cite the source file and line for claims the output doesn't show. (House style)
- Cut filler. (House style; global writing rules)

**Teaching approach**

- Move from simple to sophisticated. (Pedagogy note; house style)
- Teach one lesson per page, and get the reader acting early. (House style)
- Show only the code the lesson needs. (House style; pedagogy note)
- Show only output captured from a real run. (This tutorial's conventions, over house style and pedagogy note)
- Use real output to correct likely misconceptions. (House style)
- Pair each page with one scenario and one operational question. (This tutorial's conventions)
- Keep content consistent with the three-moments idea. (This tutorial's conventions)

**Page structure** (house style unless noted)

- Every page has a nav block.
- Pages link in one reading order, from the index through how-to-choose. (This tutorial's conventions)
- Lesson pages keep sections in the standard order, with a "Why you are here" note of at most two sentences.
- The first command appears early on the page.
- Pages run 200 to 750 words.
- Steps follow the standard structure: label, command, expected output.
- Blocks carry **Command:** and **Expected output** labels.
- Each step ends with a "What it means" or "What you are looking at" callout.
- A request body or query appears once.
- Console directions are bullets. (House style; this tutorial's conventions)
- Deep dives have question headings and a summary with a link in the body.
- Part landing pages follow the standard form. (House style; this tutorial's conventions)
- The reference page records what was verified.
- The README and TUTORIAL.md contain the standard elements.

**Formatting** (house style unless noted)

- Each callout type is used for its purpose.
- Mermaid diagrams carry a caption.
- Code blocks use the right fence type.
- Bash blocks contain only runnable commands, with no prompts or output.
- Bold and inline code are used consistently.
- Links and anchors resolve. (House style; this tutorial's conventions)
- Any step that reads an environment variable exports it. (Set-the-env-you-read note; review skill)

**Facts specific to this tutorial** (all from this tutorial's conventions)

- A single agent emits six metrics; the seventh needs the `Workflow` primitive.
- `error.type` is stamped only because the demo wraps its tools in `StatusAwareTool`.
- Scripts must call `force_flush()` to export their metrics.
- The experimental metrics are off unless `ADK_EXPERIMENTAL_TELEMETRY` is set.
- A standalone script exporting to Cloud Monitoring needs `gcp.project_id` in its resource.
- PromQL queries dotted histograms in the quoted brace form with `_sum`, `_count` and `_bucket` suffixes.
- The task-outcome counter on page 3.7 is gated behind `TUTORIAL_OUTCOME_METRIC`.
