# ADK tracing tutorial: review

Reviewed 2026-10-02 against google-adk 2.8.0 (the pinned version), the `tutorial-style` skill, and `ai/adk/tracing/CLAUDE.md`. Read-only: no tutorial files changed. Paths are relative to `ai/adk/tracing/`.

Each page was read for clarity, fact-checked against the installed ADK source and Google's docs, and rerun end to end on a scratch project (`jwd-dev-1` to `jwd-dev-4`, never `jwd-gcp-demos`). Items marked ✔ were reproduced in that rerun.

**Bottom line.** The tutorial's lessons hold: in Parts 1, 3, and 4, the main demos produced the trees, ids, and log matches the pages show. The problems are in getting there. Part 2's deploy pages fail as written, many steps leave out a command the reader needs, and eight claims are false (blockers 3, 4, 8, 9, 13, 14, 20, 21).

**Names used below.** The tutorial runs three small servers. This review calls them by the tutorial's own names:

| Name | File | What it adds |
|---|---|---|
| `02` server | `examples/02_trace_server.py` | Sends spans to Cloud Trace; returns the trace id from `/chat` |
| `03` server | `examples/03_correlated_server.py` | `02` plus a logging handler that attaches span ids to your log lines |
| `04` server | `examples/04_propagated_server.py` | `03` plus reading the caller's trace header, so one request is one trace |

## Blockers: steps that fail, and claims that are false

| # | Where | Now | Problem | Fix |
|---|---|---|---|---|
| 1 | 2.2 Step 1 | Deploys with `adk deploy cloud_run … --otel_to_cloud .` from the tutorial folder. | ✔ The tutorial folder holds no agent, so the service serves nothing (`/run` returns 404). Deploying `demo_agent` instead crashes on boot: that folder has no `requirements.txt`, so the trace exporter packages are missing. The page's captured output came from a different deploy: the `02` server built from `deploy/Dockerfile.trace_server` with `gcloud run deploy`. | Rewrite the page around the deploy that was captured: copy `deploy/Dockerfile.trace_server` to `./Dockerfile`, run `gcloud run deploy` with `--set-env-vars`, delete the copy afterward. **Status:** done (captured on jwd-gcp-demos). |
| 2 | 2.2 Step 2 | "Send one London turn to the service URL, take its trace id." No command. | ✔ The service needs an identity token, and the reader isn't told. The turn fails with a model 404 because the deploy sets `GOOGLE_CLOUD_LOCATION=us-central1`, where the model doesn't exist. `OTEL_SERVICE_NAME` is never set. | Set `GOOGLE_CLOUD_LOCATION=global` and `OTEL_SERVICE_NAME=adk-tracing` in the deploy command. Add a `curl` to `/chat` with `-H "Authorization: Bearer $(gcloud auth print-identity-token)"`. **Status:** done. |
| 3 | 2.3, "Exported" step | Pointing `TUTORIAL_TRACE_ENDPOINT` at a closed port is said to make the trace read back as nothing. | ✔ The trace still reaches Cloud Trace (7 spans). That variable adds a second exporter beside the Google one; it doesn't replace it. Only the extra export fails, and each turn slows to 12–20 s while it retries. Page 2.6 correctly calls the variable "additive", so the two pages contradict each other. | Say what happens: the turn answers, the server logs `Connection refused`, turns slow down, and the trace still arrives. To show a trace that never lands, use the step that removes the resource (it already produces a 400 and no trace). Fix the same claim in the `02` server's docstring and comment at lines 19–21 and 97–98. **Status:** done; `scenarios.md` row fixed too. |
| 4 | 2.3, "Recorded" step | "An all-zeros id in the `/chat` response is the tell: nothing was recorded." | ✔ With no trace provider installed, the `02` server returns HTTP 500 (`'ProxyTracerProvider' object has no attribute 'force_flush'`), not an all-zeros id. | "With no provider, `trace.get_current_span()` returns a placeholder span whose id is all zeros. The `02` server fails earlier, with a 500." **Status:** done. |
| 5 | 2.4 Step 3 (teardown) | `vertexai.init(...); [e.delete(force=True) for e in vertexai.agent_engines.list()]` | ✔ Raises `AttributeError: module 'vertexai' has no attribute 'agent_engines'`. With the import fixed, it deletes every Agent Runtime engine in the project, including other people's. | Delete only the engine this page created: `from vertexai import agent_engines`, then `agent_engines.get("projects/$PROJECT_ID/locations/$REGION/reasoningEngines/$ENGINE_ID").delete(force=True)`. **Status:** done; tested on jwd-dev-3 and jwd-gcp-demos. |
| 6 | 2.4 Steps 1–2 | Expected tree has 4 spans; the page says the tree under `invoke_agent` "looks as it does everywhere else" and "came out complete". | ✔ Four spans, because the model call failed: the engine has no `GOOGLE_CLOUD_LOCATION`, so it calls `us-central1` and gets a 404. A successful turn has 7 spans. The page says the deploy reads `demo_agent/.env`, but that file doesn't exist and no step creates it. | Tell the reader to create `demo_agent/.env` with `GOOGLE_CLOUD_LOCATION=global`, then recapture the 7-span tree. Add the missing command that sends the turn (`agent_engines.get(...)` then `async_stream_query`). **Status:** done; 7-span tree recaptured. |
| 7 | 2.5 Do this | Two `export` lines, then "Then fire the load and count roots." | ✔ No command restarts the server (the sampler is read at startup), sends the 20 turns, or counts the kept traces. The expected output came from a separate script the reader never sees. The rerun with real commands gave 20/20 kept by default and 10/20 at a 0.5 ratio. | Add the three commands: restart the `02` server, `./load/turns.sh baseline 20`, then count with `./trace/list_traces.sh 'span:invoke_agent' 20`. **Status:** done, with a different count: dropped turns now print `trace=—`, so the page counts returned ids and matches them in `list_traces.sh` (a time-window count also caught other tutorials' traces). |
| 8 | 1.4 deep dive; `how-to-choose.md` line 65 | "The exception message never lands on the span, so the city name does not leak." | ✔ False, and it's a privacy claim. ADK calls `span.record_exception(error)` (`google/adk/telemetry/tracing.py:281`), which stores `exception.message` and the full stack trace on each `exception` event. Only the span's status and `error.type` leave out the message. | "`error.type` and the status hold only the class name, but each `exception` event stores the message and stack trace, so the city name does land on the span." **Status:** 1.4 done; `how-to-choose.md` pending. Rerun also showed both tool-span events are `LookupError`, not `DynamicNodeFailError`; fixed. |
| 9 | 1.6 | "`asyncio.create_task` … runs on a fresh context and does not inherit the current span." | ✔ False. `create_task` copies the current context, so the span nests correctly. Work on another thread (`threading.Thread`, `loop.run_in_executor`) is what loses it. | "The one place it breaks is work on another thread, such as `threading.Thread` or `loop.run_in_executor`. Wrap it in `contextvars.copy_context().run(...)`. `asyncio.create_task` and `asyncio.to_thread` already copy the context." **Status:** done. |
| 10 | 3.1, 3.2, 3.3, 4.3 | `gcloud logging read 'trace="projects/'"$PROJECT_ID"'/…"'` with no `--project` flag. | ✔ `gcloud logging read` searches gcloud's default project, not the one in the filter. Setup never sets that default. A reader whose default differs from `$PROJECT_ID` gets empty results. 4.3's saved filter also hard-codes `projects/jwd-gcp-demos`. | Add `--project="$PROJECT_ID"` to every `gcloud logging read`, and use `$PROJECT_ID` in 4.3's saved filter. **Status:** Part 3 done; 4.3 pending. |
| 11 | 3.4 deep dive | Reproduces the sampling problem with a `curl` that sends `traceparent: …-00`, then says the default sampler records zero spans. | ✔ The `curl` has no `content-type` header, so FastAPI rejects it with HTTP 422. Even with the header, the `04` server already sets `OTEL_TRACES_SAMPLER=always_on` (line 43), so the request records the full tree. The page shows that fix as a shell `export`, but `04` sets it in Python. | Add `-H 'content-type: application/json'`. Tell the reader to stop `04`, `export OTEL_TRACES_SAMPLER=parentbased_always_on`, restart, and send the request: `get_trace.sh` then returns "Trace not found". Show the real line from `04` in a `python` block. **Status:** done; recaptured on jwd-gcp-demos (Trace not found). |
| 12 | 3.3 Step 1 | "Send a `slow-tool` (forecast) turn." | ✔ `./load/turns.sh slow-tool 1` sends London. The forecast is turn 2. The expected `fetched 3-day forecast` line never appears. | "Send two `slow-tool` turns (`./load/turns.sh slow-tool 2`) and read the second." **Status:** done; recaptured. |
| 13 | 3.3; Part 3 index diagram | 3.3: "That access log is exactly what 3.4 puts inside the trace." The diagram routes uvicorn through the same logging handler. | ✔ uvicorn's access log never reaches Cloud Logging (uvicorn sets it not to propagate; 3.3's own capture shows this). Page 3.4 joins Cloud Run's request log, a different entry. | 3.3: "Cloud Run's request log is a separate entry, and 3.4 puts that one in the trace. The uvicorn access line stays out of Cloud Logging." Remove uvicorn from the diagram's handler arrow. **Status:** done. |
| 14 | 3.5, way B | The `google-cloud-logging` handler "reads a `traceparent` or `X-Cloud-Trace-Context` header when no span is current (`_helpers.py:226-260`)". | The cited lines are a different function. The header fallback exists only for Flask and Django requests (`_helpers.py:65-135`, `238-284`), so this tutorial's FastAPI servers get none. The table also merges two handlers: `CloudLoggingHandler` sends through the Logging API, and `StructuredLogHandler` writes JSON to stdout. | State the Flask and Django limit with the right lines. Split the table cell into the two handlers. **Status:** done; also added a Not verified table. |
| 15 | 3.2 Step 3 | Command: `gcloud logging read '… AND severity=WARNING'`. Expected output shows five fields: `severity`, `trace`, `spanId`, `traceSampled`, `message`. | ✔ Without `--format`, gcloud prints a dozen fields as YAML, and the message key is `textPayload`, not `message`. | Add `--format='yaml(severity,trace,spanId,traceSampled,textPayload)'` and rename `message` to `textPayload` in the output. **Status:** done; recaptured (gcloud yaml sorts keys, so the order differs from the proposal). |
| 16 | 4.4 Step 3 | Filters on `gen_ai.conversation.id:42e24c76-…` "from this turn". | The reader has no way to get that id: the `03` server's `/chat` returns only the answer and the trace id, and `turns.sh` prints only the trace id. | Add a step that reads the id from the trace (`curl` the trace and `grep conversation.id`), or filter on `'span:"execute_tool get_weather"'`, which the reader can use as is. |
| 17 | 4.3 Step 2 | The second shell runs `export HOST` and `export ENDPOINT` only. Steps 3 and 4 then use `$PROJECT_ID`. | `$PROJECT_ID` is empty in that shell. Pages 4.1, 4.2, and 4.4 start their second shell with `source env.sh`; 4.3 doesn't. | Add `source env.sh` as the first line. |
| 18 | `02` and `03` servers | `/chat` returns the trace id, which `turns.sh` prints. | ✔ About 1 turn in 6 prints `trace=—` (an empty id), seen in the Part 2, 3, and 4 reruns. The id is captured on the exporter's background thread, and the request sometimes reads it before that thread runs. Pages then hand the reader nothing to look up. | Read the id from the current span inside the request handler, as `04` does. Until fixed, add "If `trace=—` appears, send the turn again." **Status:** done, differently: `02` and `03` have no server span, so the current span in the handler is all zeros. A span processor now maps `gen_ai.conversation.id` to the trace id on span end; 22/22 turns returned an id, including concurrent ones. |
| 19 | `trace/get_trace.sh` | Prints each span with its duration. | ✔ Durations are blank for traces from Cloud Run and Agent Runtime. Their timestamps have nine fractional digits, Python's `strptime` accepts six, and the error is swallowed. This is why 2.2 and 2.4 show no durations. | Trim to six digits before parsing: `re.sub(r'(\.\d{6})\d*Z', r'\1Z', t)`. **Status:** done. |
| 20 | 2.6 | Lists Honeycomb among "the agent-observability vendors on the adk.dev integrations list", and says vendors read ADK spans "without a translation layer" because they follow the GenAI convention. | The adk.dev list has 15 vendors and no Honeycomb. ADK spans carry many `gcp.vertex.agent.*` attributes that are not part of that convention. Nothing on the page was run, and it has no **Not verified** table. | "Any OTLP backend, such as Honeycomb, accepts the spans. Check the vendor's ADK page for how it maps attributes." Add a **Not verified** table. **Status:** done. |
| 21 | 4.6 | "The `slow-tool` turn with `TUTORIAL_CUSTOM_SPAN=1` adds one more [span]." | Only forecast turns call the forecast tool, and `slow-tool` alternates London and forecast turns. | "A forecast turn with `TUTORIAL_CUSTOM_SPAN=1` has eight spans." |

## Steps the reader cannot follow

These steps omit a command, a value, or an instruction the reader needs.

| Where | Problem | Fix |
|---|---|---|
| 3.1–3.4 | All three servers use port 8080. No page says to stop the previous server before starting the next, and 3.2 Step 3 and 3.4 Step 1 give no command to start `03` or `04`. | Add a **Command:** each time the server changes: stop the old one, start the new one, keep any needed exports (3.2 needs `TUTORIAL_CLASSIFY_ERRORS=1` still set). **Status:** done. |
| 2.1, 3.1, 3.2, 3.3, 4.4 | Commands contain trace ids from the author's run (`8e95a681…`, `6cbc244c…`, `ae6b5c65…`, `497cc8ea…`) with no instruction to swap in the reader's own. | Before each such command: "Replace the trace id with the one your turn printed." |
| 4.1 teardown | Ends with "Press Ctrl+C … Nothing was created in the cloud." | `HOST`, `ENDPOINT`, `START`, and `TUTORIAL_CUSTOM_SPAN` stay set and change how 4.2 and 4.3 behave. Add `unset TUTORIAL_CUSTOM_SPAN HOST ENDPOINT START`. |
| 4.1 Step 3 | The trace list URL has no `pageSize`, and the page says all ten forecast turns came back. | The API returns 10 traces per page by default, so an eleventh would be silently cut. Add `&pageSize=100`. |
| 2.1 Step 2 | "Take the trace id from the dev UI's **Trace** tab (or the debug endpoint)." | The endpoint isn't named, and it returns the id as a decimal number that `get_trace.sh` can't use. Name it (`/dev/apps/demo_agent/debug/trace/session/<session_id>`) and give the conversion: `python3 -c "print(format(<id>, '032x'))"`. **Status:** done. |
| 2.3 Step 1 | The server runs in the foreground; the next command is in the same block of steps. | Say "In a second terminal". Do the same anywhere a server is running (2.1, 3.1–3.4). |
| 2.3 | "Comment out the span processor" and "Drop `otel_resource=…`". | There is no single span-processor line, and the reader is editing a tracked file without being told which lines. Name them: `examples/02_trace_server.py:110`, inside `install_cloud_tracing`. **Status:** done (line 99 after the capture change). |
| 2.3 | `export TUTORIAL_TRACE_ENDPOINT=…`, then "Restore the endpoint, restart." | Add `unset TUTORIAL_TRACE_ENDPOINT` and the restart command. **Status:** done. |
| 3.3 deep dive | Negative controls 2 and 3 are hand-written log entries, and 4 is a concurrency check. No commands are given. | ✔ All four hold when run. Add the `curl` to the Logging `entries:write` API for 2 and 3, and the per-trace `gcloud logging read` for 4. **Status:** done; commands run on jwd-gcp-demos, scratch log deleted. |
| 4.2 Step 4 | Compares the trace with content capture off against "the Step 3 trace", which held the full prompt. | The run record shows the full prompt on the Step 1 conversation's fifth turn, and the reader never sees it. Point to that trace and add the `grep` that shows the prompt. |
| 00-setup | `jq` is used in 1.5 but not listed. A leftover `OTEL_EXPORTER_OTLP_ENDPOINT` makes the "local" Part 1 scripts send spans to it. | Add `jq` to prerequisites. Add: "Unset any `OTEL_EXPORTER_OTLP_*` variables. ADK adds an exporter when they are set." **Status:** done. |

## Output that doesn't match its command

| Where | Problem | Fix |
|---|---|---|
| 1.1, 1.4, 1.6 | Trees and one-line summaries appear under **Expected output**, but `01_console_spans.py` writes only JSON. 1.1's forecast tree and 1.6's tree also drop the `invocation` root and the `generate_content` spans while saying "the same shape". | Label each as "drawn from `out/spans.json` (trimmed)", or add the `jq` command that prints it. **Status:** done (labeled as drawn or trimmed). |
| 1.2 | The JSON excerpt shows `"resource": { "attributes": {} }` and looks complete. | ✔ After `source env.sh` the resource is `{"service.name": "adk-tracing"}`, and the real span has four more attributes. Show the real resource and add "(trimmed to the fields this page uses)". **Status:** done (rerun on jwd-dev-3). |
| 00-setup, 1.2 | Expected output shows the agent's answer, then "(spans written to out/spans.json)". | ✔ The spans line prints first, at startup. Swap them. **Status:** done. |
| 1.4 Step 1 | Expected output is only the `AGENT:` line, yet the next callout points to the tool's WARNING on the terminal. | ✔ Add the line it prints: `weather lookup failed for 'Atlantis': no data`. **Status:** done. |
| 1.4 deep dive | "Three spans go red" with no other change noted. | ✔ The raised-error run has 5 spans, not 7, because the model never receives the tool result, and the script exits with a traceback. Say both. **Status:** done. |
| 3.4 Step 1 | The local tree is hand-drawn ("parent → (the inbound header's span)") with no command. | ✔ The real tree has 11 spans, including `http receive` and two `http send`. Show `get_trace.sh` output, or label the block "illustrative (trimmed)". **Status:** done: labeled illustrative (trimmed) with the real 11-span shape named; the fixed header id would append to an existing trace if recaptured. |
| 4.1 Step 5 | "A forecast turn averaged 1.19 s longer … the tool averaged 1.08 s of that, while model time per turn moved 0.11 s." | ✔ Didn't reproduce: one 19 s model call made forecast turns shorter on average. Medians matched (1.23 s longer). Use medians, and say one slow model call can swamp the tool's second. |
| 4.1, 4.3 Step 1 | "Application startup complete." appears before "Exporting spans …". | The server prints the export line first. Swap them. |
| 4.4 | `(1 traces)` appears before the trace id. | `list_traces.sh` prints the count last. Move it. |
| 3.1, 3.2, 4.1–4.3 | Console steps (the **Logs & Events** tab, **View logs**, the **Grouped** tab, the **Span status** filter, red bars, **Inputs/Outputs**) are stated as results. | Nobody has clicked them; the run records say so. Add "These steps follow Google's docs; the commands below confirm the same facts." The publishing gate in the plan still requires one person to click **Logs & Events** on page 3.2's trace. |

## Claims that go further than the evidence

| Where | Says | Problem and fix |
|---|---|---|
| TUTORIAL.md; Part 3 index; 3.1 note | "The join is one field." | A log entry matches a span through two fields, `trace` and `spanId` (3.1's deep dive says so). Say "two fields" everywhere. |
| TUTORIAL.md | "Nothing leaves the process until you install an exporter." | Setting `OTEL_EXPORTER_OTLP_ENDPOINT` also sends spans, with no code. Add "or set an OTLP endpoint". |
| 00-setup | "Two latencies are the whole reason the tree has shape." | ADK builds the tree; the latencies only make the slow step visible. Say that. **Status:** done. |
| scenarios.md | `slow-tool` "adds about 1 s per turn". | The tool sleeps 0.3–1.5 s. "adds 0.3–1.5 s; the two model calls still take most of the turn." |
| 1.3 | `gen_ai.*`: "Metadata, not content." | True for spans only; the log events carry content when it's enabled. "On spans, metadata only." **Status:** done. |
| 1.4 | "Three different ways", over a four-row table. | Keep three rows and explain the `{"error": …}` case below it, or retitle "Four tool behaviors". **Status:** done: retitled the table and explained the fourth row. |
| 1.6 | "It is three lines." | The block has four lines of code. **Status:** done. |
| 2.1 | The local tree "is byte-for-byte the tree Cloud Trace now holds". | Same spans and parents; ids and durations differ. "The same seven spans and parent chain." **Status:** done. |
| 2.2 | "A service you deployed and never instrumented." | The captured service was the `02` server, which instruments itself. Tie the claim to whatever 2.2 ends up deploying. **Status:** done. |
| 2.4 | The deploy "rewrites the pushed `requirements.txt`, turning `google-adk[otel-gcp]` into `google-adk[a2a]`". | `demo_agent/` has no `requirements.txt`, so the deploy creates one with only `google-adk[a2a]`; the root file is never sent. Say that. **Status:** done. |
| 2.4 | Says nothing about content capture. | `--otel_to_cloud` on Agent Runtime also sets `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` (`cli_deploy.py:1281-1282`), the opposite of 1.3's default. Add a note. **Status:** done. |
| 3.2 | "The bridge is one line of setup." | It's three lines (`03_correlated_server.py:95-97`), and the page never shows them. Show them in a `python` block. **Status:** done. |
| 3.4 | Propagation "deletes" traces; "you can lose almost every trace". | Nothing is deleted; the spans are never recorded. "Propagation can silently stop your traces from being recorded." **Status:** done. |
| 3.5 | "The `ContextVar` trick … is not needed with any of these." | `03` and `04` both use one, to hand the trace id back to `/chat`. Say logs don't need it; the servers use it only for the response. **Status:** done; after blocker 18 neither `03` nor `04` uses a ContextVar, so the page says `02` and `03` keep a session map. |
| 4.3 deep dive | "The trace and the entry age out after 30 days; the command and the expectations do not." | The saved command hard-codes the trace and span ids, so it returns nothing after 30 days. "Swap in the new ids each run; the expectations stay the same." |
| 4.4 | Script output is "the same tree the Trace Explorer waterfall draws". | It was compared only against the raw API response, not the console. Say that. |
| 4.6 | "Tracing every turn is on by default, and so is the prompt text on every span." | Spans reach Cloud Trace only when exported, and Agent Runtime turns content off. "ADK always opens the spans. Once you export them, the prompt rides on every span unless you turn it off." |
| `examples/_common.py` docstring | "The same [setup helper] `adk web` uses." | Plain `adk web` builds a bare provider; it uses this helper only with `--otel_to_cloud` (`api_server.py:648-668`). |
| how-to-choose.md | Verification table: 4.4 has "none" unobserved; 4.1 and 4.2 list only some console steps. | 4.4's console comparison was never done, and `list_traces.sh` was broken until a same-day fix. Add the missing console steps to 4.1 and 4.2. Add a **Not verified** row for the `adk-python` `main` claims, which have no run record. |

## Shorthand to replace

| Term | Where | Replace with |
|---|---|---|
| "the M3 deck" | 1.3 | Delete. The reader has never seen it. **Status:** done. |
| "bridge", "stamp" | Part 3 index, 3.1–3.5 | Define once on the Part 3 index: "a logging handler that copies the current span's ids onto each log record". **Status:** done. |
| "rung", "ladder" | 2.3, scenarios.md, how-to-choose.md | "step", and name each step ("recorded", "exported", "visible") the first time. |
| "knob" | 1.3, 2.6 | The variable's name. |
| "flyout" | 3.1, 4.2 | "the trace details panel" |
| "reader" (for exporter) | Part 1 index | "exporter" **Status:** done. |
| "spine of the tutorial" | TUTORIAL.md, scenarios.md | "lists every experiment the tutorial runs" |
| "Negative controls", "found by nothing", "the span *is* the context" | 3.3, 3.5 | "Lines that look correlated but aren't", "no span query returns it", "the current span carries the ids" **Status:** done. |
| "trap", "payoff", "known-good failure" | 2.5, 3.2, 4.3 | Say the outcome: "Part 3's propagation can drop every trace", "the rest of the part reuses this", "a reference for how the failure should look" |
| "a page at 3 a.m." | Part 4 index | "the questions an on-call alert raises" |
| Bare `02`, `03`, `04` | Part 4 pages, scenarios.md | The file name on first use per page. |
| "Stage 0 probes", "run record" | 2.4, how-to-choose.md | Plain words; these are authoring terms. **Status:** 2.4 done. |
| Four names for one product | 2.4 | Agent Runtime, Vertex AI Agent Engine, Agent Engine, Agent Platform. Pick one; mention the console's name once. **Status:** done. |
| Undefined terms | 1.1, 2.5, 3.4 | Define on first use: span ("one timed operation, such as a model call"), propagator ("reads the trace id from an incoming header"), sampler ("decides which traces are kept"), `ParentBased(ALWAYS_ON)` ("keep every root span; follow the parent's decision for child spans"). |

## Cross-cutting style

| Rule | Status | Fix |
|---|---|---|
| Links name the page they point to | 1.4, 1.5, 2.5, and 3.2 label links "4.2", "4.3", "4.6", "3.4" but point to part index pages. 2.2 writes "page 3.4" without a link. | Link the page itself. |
| Source citations use the full path | Bare `tracing.py`, `cli/cli_deploy.py`, `_helpers.py` across 1.1–1.6, 2.1, 3.1, 3.5; 4.5 cites `(:5943)` with no file. Several line numbers are off by one or two (`fast_api.py:312` is `:314`). | Use `google/adk/telemetry/tracing.py:229` style and recheck each line. |
| Word budget 200–750 | 4.1 has 834 words and 4.2 has 857. Part indexes run 292–332 against a 200 target. | Cut 4.1 Step 3 (4.4 teaches the list call). Move 4.2 Step 4 (content off) to 4.6. Trim index paragraphs that repeat their tables. |
| One lesson per page | 3.4 teaches propagation, the Cloud Run view, and the sampling problem. 4.2 teaches session search, trace search, and content off. | Move the extra lessons to deep dives or the page that owns them. |
| **Command:** and **Expected output** labels | Missing in 00-setup "Verify it runs", 1.2, 1.3, 1.4 deep dive, 2.3 Step 2, 3.1, 3.2's second shell. | Add them. |
| Console directions as bullets | 1.1 Step 1 and 4.2 Step 4 are paragraphs. | One action per bullet, UI element in bold. |
| Deep dive headings are questions | 1.3, 1.5, 1.6, 4.3 | "Is there a second content setting?", "Which ids does a turn carry?", "How do I keep a failure as a reproduction?" |
| Why you are here: ≤ 2 sentences | 1.5 has three. | Trim. |
| No bold for emphasis | 1.4 bolds a whole sentence; 3.4 bolds "equals the header's". | Plain text. |
| One term per concept | Parent spans are "UNSET" in 1.4's text and "OK" in its table and scenarios.md. The Part 4 index says "Grouped table" and "heatmap"; 4.1 says "Grouped tab". Placeholders are `your-project-id` and `your_project`. | Pick one of each. |
| Say each fact once | 30-day retention appears in 4.4, 4.6, and how-to-choose. The content-setting table appears in 4.6 and how-to-choose with different line ranges. The three agent switches are explained in setup, scenarios, and each page. | Keep one copy and link to it. |
| Name likely surprises | `adk web --otel_to_cloud` logs repeated `Failed to export metrics batch … 400`. Every run prints `UserWarning: [EXPERIMENTAL] … JSON_SCHEMA_FOR_FUNC_DECL`. On `03`, the tool's WARNING stops printing to the terminal. | One line each: the first two are harmless for traces; the third is expected, because the log now goes to Cloud Logging. |

## Code and scripts

| File | Problem | Fix |
|---|---|---|
| `examples/03_correlated_server.py:20-22` | Docstring says to run `turns.sh returned-error 1` with the classify switch on; page 3.2 runs `classified-error`. | Use `classified-error`. **Status:** done. |
| `examples/04_propagated_server.py:76-96` | The trace-id capture code and its extra span processor are never used: `/chat` reads the id from the current span. A `try`/`except` guards an import that `requirements.txt` already pins. | Remove both, so the file shows only the three additions page 3.4 teaches. **Status:** done. |
| `deploy/Dockerfile.trace_server` | Comment says it's used by 2.3 on Cloud Run. 2.3 never deploys, and 2.2 doesn't mention the file. | Update after fixing 2.2. **Status:** done. |
| `trace/list_traces.sh` | Header says "one id per line"; it prints `<id>  N spans`. | Fix the header. **Status:** done. |
| `demo_agent/agent.py` | The three `TUTORIAL_*` switches turn on for any non-empty value, including `0`. | Say so in setup, or check for `1`. **Status:** done: gates now check for `1`. |

## Demo reruns

All runs used google-adk 2.8.0 with every variable exported. The `.env` files name `jwd-gcp-demos`, but none overrode an exported value: the examples load `.env` without overriding, and `adk web` re-applies values already set (`google/adk/cli/utils/envs.py:81-82`). Nothing ran in `jwd-gcp-demos`.

| Part | Project | Result |
|---|---|---|
| Setup, Part 1 | jwd-dev-1 | All demos match: the 7-span tree, the three error cases, content off, five turns with one conversation id, the custom span. Differences are display only (listed above). |
| Part 2 | jwd-dev-2 | 2.1 and 2.3's baseline match. 2.2 fails as written (blockers 1–2). 2.3's outage and recorded steps don't behave as described (blockers 3–4). 2.4 deploys and reads back a 4-span tree from a failed model call (blocker 6). 2.5 matches once the missing commands are supplied. |
| Part 3 | jwd-dev-3 | All log matches hold, including negative controls 2–4, which had never been run. The 3.4 deep-dive `curl` fails (blocker 11); with it fixed and the default sampler set, zero spans are recorded as claimed. |
| Part 4 | jwd-dev-4 | All commands match once `--project` is added to `gcloud logging read`. 4.1's ranking holds (model spans p50 2.10 s, tool p50 0.90 s); its mean-based sentence doesn't. |

**Not rerun:** browser steps in Trace Explorer, Logs Explorer, and the dev UI (the same data was read through the APIs); 2.4's teardown as written (it would delete other engines); 3.4's Cloud Run tree (the page doesn't ask the reader to deploy); setup's 403 troubleshooting (it would hit `jwd-gcp-demos`). Nothing was skipped for cost; total spend was under $1.

## Cleanup and repo state

| Item | State |
|---|---|
| Cloud Run service `adk-trace`, its image, and source zips (`jwd-dev-2`) | Deleted |
| Agent Runtime engine `3745815663751462912` (`jwd-dev-2`) | Deleted |
| Traces and log entries in `jwd-dev-1` to `jwd-dev-4` | Left; they expire on their own |
| Log `p3-neg` in `jwd-dev-3` (two hand-written test entries) | Left. Delete with `gcloud logging logs delete p3-neg --project=jwd-dev-3` if wanted. |
| Engine `7194447078410420224` in `jwd-dev-2` | **Check this.** It existed before the review and was gone afterward. No review agent targeted it or deployed any other engine. |
| `git status` | Unchanged by the review apart from this file. `ai/adk/logging/Dockerfile` appeared as untracked at 11:59. It's a copy of the logging tutorial's plugin-job Dockerfile, and no review agent reports creating it. Left untouched. |

## Suggested order

1. **Fix the false claims (blockers 8, 9, 13, 14, 20, 21).** Text-only, with no runs needed.
2. **Fix the scripts and code (blockers 18, 19; Code and scripts).** Every later recapture depends on them.
3. **Add the missing commands.** That's `--project`, the server switches, the id substitutions, and the env `unset` lines (blockers 10–12, 15–17; Steps the reader cannot follow).
4. **Rework Part 2 (blockers 1–7) and recapture 2.2 and 2.4 live.**
5. **Style pass:** shorthand, labels, links, citations, budgets.
6. **Console check:** click through **Logs & Events** and the other console steps once, then update the verification table in `how-to-choose.md`.

---

## Appendix: review rubric

The review applied these rules, merged from the `tutorial-review` skill, the `tutorial-style` skill, `ai/adk/tracing/CLAUDE.md`, the Writing section of `~/.claude/CLAUDE.md`, and the tutorial pedagogy note.

### Rules this review found broken

| Rule | Source | Pages |
|---|---|---|
| Every claim matches the pinned ADK, Google's docs, and a real run | tutorial-review skill | 1.4, 1.6, 2.2–2.6, 3.3, 3.5, 4.4, 4.6, scripts |
| Output comes from real runs; anything else is labeled | tutorial-style; pedagogy note; tutorial CLAUDE.md | 1.1, 1.2, 1.4, 1.6, 2.2, 2.4, 2.5, 3.1, 3.2, 3.4, 4.1–4.4 |
| Each demo, rerun, matches its page | tutorial-review skill | 2.2, 2.3, 2.5, 3.2, 3.3, 3.4, 4.1, 4.4 |
| A step that reads a variable sets it | tutorial-review skill; memory "set the env you read" | 3.2, 4.1, 4.3 |
| Clean up what the page creates, and only that | tutorial-review skill | 2.2, 2.4 |
| Each page's story holds together | tutorial-review skill | most pages |
| No shorthand | tutorial-review skill | every part |
| Cite source as `path/file.py:line` | tutorial-style | 1.1–1.6, 2.1, 3.1, 3.5, 4.5 |
| One lesson per page; 200–750 words | tutorial-style | 3.4, 4.1, 4.2, part indexes |
| **Command:** and **Expected output** labels | tutorial-style | 1.2, 1.3, 2.3, 3.1–3.4 |
| `export` on its own line, `unset` after | tutorial-style | 2.3, 3.4, 4.1, 4.3 |
| Reference pages list what wasn't verified | tutorial-style | 2.6, 3.5, how-to-choose |
| Links point to the page they name | tutorial-style | 1.4, 1.5, 2.2, 2.5, 3.2 |

### Conflicts between sources

| Topic | Applied | Overrode |
|---|---|---|
| Em dashes | tutorial-style: only in `**Step N — …**` labels | Global writing rule allowing one or two per large section |
| Which project demos use | tutorial-review skill: scratch projects only, never `jwd-gcp-demos` | Tutorial CLAUDE.md: captures come from `jwd-gcp-demos` (that rule governs writing the pages, not reviewing them) |
