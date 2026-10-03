# ADK logging tutorial review, 2026-10-02

**Scope:** everything under `ai/adk/logging/`: the README, TUTORIAL.md, Setup, Parts 1 to 6, the how-to-choose reference page, and the scripts the pages run. The review read the working tree on the `tracing-tutorial-wip` branch, including uncommitted changes.

**Versions checked against:** google-adk 2.8.0 and google-genai 2.21.0 on Python 3.13, as reported by `.venv/bin/pip show`.

**Method:** each part got three reviewers. One read it as a new student, checking writing and logic. One checked every factual claim against the installed SDK source and the public docs. One reran every demo the part asks the reader to run, on a dev project of its own. The most serious claims were then checked again in the source.

**Path conventions:** file paths are relative to `ai/adk/logging/`. A path starting with `cli/`, `telemetry/` or `models/` means the installed ADK package, `.venv/lib/python3.13/site-packages/google/adk/`. Page numbers such as "5.2" refer to tutorial pages, and line numbers refer to the file named in each section's heading.

**Fix status (added 2026-10-02):** each finding carries an ID and a Status. The review was written against an older branch, so findings were first triaged against `main` as `fixed on main`, `still real`, or `not applicable`, then updated to `done` or `skipped: <reason>` as fixes landed on branch `adk-logging-review-fixes`.

## Verdict

| Part | Demo results | State of the part |
|---|---|---|
| Setup and Part 1 | Every demo ran. 1.3's WARNING step printed INFO lines, because a leftover `demo_agent/.env` set `LOG_LEVEL`. 1.6's engine logs never appeared in the dev project. | Close. Fix the stale captures, add teardown steps to 1.4 and 1.5, and split 1.6, which is more than twice the length limit. |
| Part 2 | Ran, and matched. | Nearly ready. A diagram label is wrong, and the fix it offers doesn't apply to `adk api_server`, the server the reader just ran. |
| Part 3 | Every demo ran, with the same structure as the pages show. | 3.2's sample output and 3.3's YAML excerpt don't match a real run. 3.4 leaves a storage bucket behind. |
| Part 4 | Every demo ran. 4.1, 4.2 and 4.3 printed different output from the pages. | Several claims are false: "all four streams", a uvicorn filter that doesn't exist, and a logger-name filter that returns nothing. |
| Part 5 | 5.1 to 5.4 ran. 5.4 printed different events from the page. 5.5 Step 4 fails: no logs reach Cloud Logging. | The two content settings and the two event formats are explained inconsistently across pages. Some 5.5 results depend on the author's gitignored `.env`. |
| Part 6 | Every demo ran and matched the pages' results. | The explanation is wrong: the deploy does pass `--otel_to_cloud` to the server, and it doesn't use `AdkApp`. No teardown for either engine. |

### Top 10 findings

1. **wrong.** Part 6 says no `--otel_to_cloud` flag reaches a server on Agent Runtime and that an `AdkApp` reads `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY`. In ADK 2.8.0, `adk deploy agent_engine` deploys a container that starts `adk api_server`, and both of Part 6's methods (the flag in 6.2, the `.env` line in 6.3) make the CLI add `--otel_to_cloud` to that start command (`cli/cli_deploy.py:1273-1292`, `:1392`). The 6.3 rerun printed "`--otel_to_cloud` is set to True by GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY". The pages' result still holds: no `gen_ai.*` logs and no traces arrived. *Status: still real.*
2. **wrong.** 5.5 Step 4 fails today. The service answers, but no `gen_ai.*` entries reach Cloud Logging, and it logs `Failed to export logs batch code: 400`. `requirements.txt` asks for `google-adk>=2.8.0`, so the image gets 2.11.0, which rejects this server's log export. *Status: still real (the `>=2.8.0` cause is fixed on main; rerun pending).*
3. **wrong.** 5.4 says the logs hide message content because of `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS`. That variable only affects spans. The logs hide content because `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` defaults to `NO_CONTENT`. 5.4 also expects one `operation.details` event per model call; the rerun got three separate event types, because the deploy doesn't opt in to the experimental format. *Status: still real.*
4. **wrong.** 4.2 says one logging config covers "all four streams", including the `uvicorn.access` filter from Part 2. `examples/06_custom_server.py` sets up neither OpenTelemetry nor that filter, and its access lines carry no trace id. *Status: done.*
5. **wrong.** 4.4 says you can filter Cloud Logging on the logger name `agent.telemetry`. The deployed server's formatter never writes the logger name, and the filter returned nothing on the rerun. *Status: done.*
6. **wrong.** Five pages create cloud resources and never delete them: 1.4 (a Cloud Run job), 1.5 (two services), 3.4 (a storage bucket holding full prompts), 6.2 and 6.3 (two Agent Runtime engines). *Status: still real.*
7. **misleading.** The gitignored `demo_agent/.env` changes results from page to page. Setup never creates it, but 1.6 and Part 6 write it, and Cloud Run images include it. On the reruns, its `LOG_LEVEL=info` overrode `--log_level WARNING` in 1.3, and its `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` hid span content in 5.2. 6.2's "restore" step writes `LOG_LEVEL=info` back into it. *Status: still real.*
8. **wrong.** 4.1 shows 3 of the 6 lines one question produces, and 4.3's table shows 6 of 8. A question that uses the weather tool calls the model twice, and several pages show only one call without saying the output is trimmed. *Status: still real.*
9. **wrong.** Two 5.5 claims hold only with settings in the author's gitignored root `.env`: the `generic_task` resource with a `job` label (needs `service.instance.id`), and `<elided>` content. A reader starting from `.env.example` sees neither. *Status: still real.*
10. **wrong.** `deploy/deploy_job.sh` and `deploy/deploy_api.sh` end by telling the reader that stderr lines get ERROR severity. 1.4 shows, and the rerun confirmed, that they arrive with blank (Default) severity. *Status: still real.*

---

## Findings by file

**Severity tags**, from most to least serious: **wrong** (a reader following the page gets an error or a false belief), **misleading** (partly true, but leads the reader to the wrong conclusion), **unclear** (a reader would have to guess what is meant), **style** (breaks the house style but does not hurt understanding). Within each file, findings are grouped by tag in the order wrong, style, misleading, unclear. The appendix lists the standards the review applied.

### README.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F001 | 47 | "The Python examples (02 to 08) are verified end to end against a real GCP project." | `examples/` holds 01–06, 08, and 09. There is no 07, and 01 and 09 are left out. The how-to-choose page says "Examples 01–09". | "The Python examples (01–06, 08, 09) are verified against a real GCP project, except the items under Not verified in [How to choose & reference](tutorial/how-to-choose.md)." | still real |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F002 | 40 | "cp .env.example .env          # then set your project / model config" | House style keeps comments out of runnable fences. | Remove the `#` comment from the fence line. Add "Then set your project in `.env`." as prose after the fence. | still real |
| F003 | 30 | "you own the `dictConfig`, with explicit `severity` and per-request trace correlation" | The phrasing is dense jargon for a table cell. | "a server where you write the logging config yourself, so every line carries a `severity` and its request's trace id." | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F004 | 5 and 32 | "Cloud Run, Vertex AI Agent Engine" and "Cloud Run and Agent Engine" | The same deploy target has two names here. The title, the TUTORIAL table, and the Part 6 H1 all say "Agent Runtime", so a reader cannot tell it is the same product. | Use "Agent Runtime" everywhere and gloss it once: "Agent Runtime (`adk deploy agent_engine`)". | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F005 | 20–32 | The Files table has no rows for `examples/09_min_api.py`, `otel/`, or `agent_runtime_byoc/` | The table lists the folder contents but skips these three. `09_min_api.py` is the server deployed in 1.5. | Add a row for each, for example "`examples/09_min_api.py` \| A bare FastAPI server with naive logging, deployed in 1.5." | still real |

### TUTORIAL.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F006 | 49 | "Every command and output block is from a real run." | The Not verified table on the how-to-choose page lists 4.3 as not verified end to end. 4.3's console table also does not match a real run. | "Every output block was captured from a real run, except the items under Not verified in [How to choose & reference](tutorial/how-to-choose.md)." | still real |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F007 | 19–20 | "Almost every…" (third purpose paragraph) | House style allows two purpose paragraphs. | Fold it into the first paragraph. | still real |
| F008 | 70 | "Ready? **[Start with Setup →](tutorial/00-setup.md)**" | It repeats "Start with **Setup**." at line 55. | Delete it. | still real |
| F009 | 46 | The diagram caption does not explain the dotted stream 3 | Stream 3 is drawn dotted and the caption never says why. | Add "Dotted: uvicorn configures this stream itself." | still real |
| F010 | 66 | The Part 5 row is a run-on list | One long sentence packs several topics together. | "Stream 4: read `gen_ai.*` events back from Cloud Logging, from a local run to Cloud Run, and control what content they capture (5.0–5.8)." | still real |
| F011 | 65 | The Part 4 row leaves out 4.4 | The page range says 4.1–4.4, but the row never mentions 4.4. | End it with "…and when a per-agent callback beats a plugin (4.1–4.4)." | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F012 | 55 | "(each page has a **Next →** link)" | The nav links read `[→ 1.2 · …]`. No link is labeled "Next". | "(each page has a → link to the next page)" | still real |

### tutorial/00-setup.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F013 | 25 and 29 | "# if you have not already", "# edit .env to contain:" | House style keeps comments out of runnable fences. | Move both comments out of the bash fences and into prose. | done |
| F014 | 43 | "**`source env.sh` again in each new terminal.**" | House style does not use bold for instructions. | Remove the bold. | done |
| F015 | 73–78 | The logger-tree diagram shows `agent.telemetry`, `uvicorn.error`, `sessions`, and `plugin_manager` | This page never explains those four nodes. | Remove those four nodes. Or caption "`agent.telemetry` is the logger you create in Part 4." | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F016 | 25 | "edit .env to contain:" | `.env.example` already holds those lines, so the copied `.env` needs only the project id changed. | "Open `.env` and replace `your-project-id` with your project." | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F017 | 30 | No mention of `demo_agent/.env` | That file is gitignored, so a fresh clone lacks it. Yet 5.4 and 6.2 read it and overwrite it. | Add "ADK's servers also read `demo_agent/.env`. Create it with `cp .env.example demo_agent/.env`." Check the wording against what 1.2 needs. | done (Setup says not to create `demo_agent/.env`; ADK falls back to the root `.env`) |
| F018 | 81 | No verification step at the end of Setup | A broken setup first shows up as a failure in 1.1. | Add a **Command:** `.venv/bin/python -c "import google.adk; print(google.adk.__version__)"` with **Expected output** `2.8.0`. | done |
| F019 | 28 | "GOOGLE_CLOUD_LOCATION=global" next to `REGION=us-central1` | Two different locations appear with no explanation of which is used for what. | Add "`global` is where the model runs. Your Cloud Run services use `REGION` (`us-central1`)." | done |
| F020 | 8 | "All commands run from this folder." | The page sits under `tutorial/`, so "this folder" points to the wrong place. | "All commands run from `ai/adk/logging/`." | done |

### tutorial/part-1/index.md

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F021 | 29 | "All four streams land together on a service" | The tutorial's fourth stream (OpenTelemetry) is covered in Part 5, not Part 1, so Part 1 never reaches it. | "Streams 1–3 land together on a service" | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F022 | 9–10 | "What `DEBUG`, `INFO`, `WARNING`, and `ERROR` each reveal" | The subtitle promises `ERROR`, but no Part 1 page runs the agent at that level. | Drop `ERROR` from the subtitle, or add an `error` run to 1.1. | done |
| F023 | 14–15 | "instead of drowning in output or flying blind" | The metaphor does not say what the reader will be able to do. | "so you can pick a level that shows what you need without burying you in output." | done |

### tutorial/part-1/1.1-test-harness.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F024 | 89 | "**Expected output** — the same run now dumps…" | House style allows an em dash only in a Step label. The same pattern recurs on other pages. | "**Expected output** (trimmed): the same run now dumps…". Do the same wherever the pattern recurs. | done |
| F025 | 46 and 51 | "**Your tool**", "**shape**" | Bold on ordinary words is not house style. | Remove the bold. | done |
| F026 | 14 | "the `google_adk` group" | "Group" is not the logging term. | "the `google_adk` logger and its children" | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F027 | 29–37, 92–104 and 138–140 | The three Expected output blocks, none labeled as trimmed | `examples/01_log_levels.py:53` prints a `===== running at INFO =====` banner first, and the blocks omit it (1.4 shows it). The DEBUG `LLM Request` block drops the `Config:`, `Text:`, and `Raw response:` sections. The rerun on jwd-dev-1 also showed `Closing runner…` and `Runner closed.` at INFO. | Keep the banner and label each block "**Expected output** (trimmed):". | done |
| F028 | 123–124 | "ADK omits auth headers from these dumps, so a DEBUG log will not leak your bearer token." | That is true only of ADK's own model dump (`google_llm.py:686-745` excludes `http_options`). Root-level DEBUG also turns on debug output from every other library. | "ADK leaves request headers out of its own model dumps. Other libraries' DEBUG output is not covered." | done |
| F029 | 143–144 | "At WARNING and ERROR a healthy run is silent." | The rerun on jwd-dev-1 printed a two-line Python `UserWarning: [EXPERIMENTAL] … JSON_SCHEMA_FOR_FUNC_DECL` on stderr at every level. It also appears in the Cloud Logging reads in 1.4 and 1.5. | "At WARNING the framework logs nothing on a healthy run. Python may still print a `UserWarning` about an experimental ADK feature; that is not a log record." | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F030 | 128 and 144–145 | "Ask about a city the tool does not know and you would see the one `WARNING` line the tool emits" | The page never runs this, and its heading promises "then ERROR", which no step shows. | Run it and show the line, or cite `demo_agent/agent.py:<line>`. Retitle the section "Turn it down to WARNING". | done |
| F031 | 19, 81 and 128 | "#### 1.1.1 Start at INFO (the default)" | House style uses `**Step N — …**` labels, not `####` headings. The page also lacks a Why you are here note and a closing handoff sentence. | "**Step 1 — Run at INFO (the default).**" and likewise for the other steps. Add the note, and end with "1.2 runs the same agent under `adk web`." | done |

### tutorial/part-1/1.2-adk-web.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F032 | 37 | "### What the flag really does" | House style writes deep-dive headings as questions. | "### What does `--log_level` do?" | done |
| F033 | 12 | "**`--log_level`**" | Bold on a flag name is not house style. | Remove the bold. | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F034 | 30–33 | "You get the same five-line lifecycle trail as the script … Same agent, same level, same logs." | The ADK CLI installs its own timestamped `file:line` format (shown in 1.3), so the lines are not the same. The page shows no output to compare. | "You get the same lifecycle events as the script, in the CLI's timestamped format (1.3 shows it)," and add a captured output block. | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F035 | Whole page | No Step label, no Expected output, no handoff; the prompt fence at lines 26–28 has no lead-in | The page does not follow the house page structure, and the prompt block appears without introduction. | Add a Step label, an Expected output block, and a handoff sentence. Put "Send this in the chat box:" before the prompt fence. | done |
| F036 | 17–18 | "open the URL it prints, pick **demo_agent** from the app dropdown, and send the same question." | The reader must carry out three separate actions from one sentence. | Split into three bullets, one action each. | done |

### tutorial/part-1/1.3-adk-api-server.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F037 | 56 | "2026-09-03 12:51:24,435 - INFO - agent.py:40 - tool get_weather called…" | The `logger.info` call is now at `demo_agent/agent.py:54`. The rerun on jwd-dev-1 printed `agent.py:54`; 1.6 shows `:53` and 6.2 shows `:54`. | Recapture the output. | done |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F038 | 27–33 and 82–88 | The curl commands put `-s -X POST` and `-H … -d` on shared lines | House style puts one flag per continuation line. | Put one flag per continuation line. | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F039 | 68–75 | The `--log_level WARNING` step, with no mention of `LOG_LEVEL` in `demo_agent/.env` | `demo_agent/agent.py:29-33` applies `LOG_LEVEL` at import, over the flag. `deploy/deploy_agent_engine.sh` (1.6, Part 6) writes `LOG_LEVEL` into that file, and the working tree's file holds `LOG_LEVEL=info`. The rerun on jwd-dev-1 confirmed it: the WARNING server printed the full INFO trail, and with `export LOG_LEVEL=warning` the output matched the page. 1.6 explains this only after the reader has run 1.3. | Add before the step: "If `demo_agent/.env` sets `LOG_LEVEL`, remove that line first; the agent applies it over the flag." | done |
| F040 | 64 | "Two formats in one stream." | The tutorial's four-streams model already uses "stream" for something else, so the reader cannot map this sentence to it. | "Two formats in one terminal. The timestamped lines are streams 1 and 2, in the ADK CLI's format. The bare `INFO:` lines are stream 3, uvicorn's access log." | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F041 | 106–112 | The TIP about `adk run` | `adk run` has nothing to do with this step and distracts from it. | Move it to a deep dive titled "### Where do `adk run` logs go?". | done |
| F042 | 111 | `tail -F "${TMPDIR:-/tmp}/agents_log/agent.latest.log"` | House style puts a **Command:** label before each command block. | Add the **Command:** label. | done |
| F043 | Whole page | No Why you are here note, no handoff, no Deep dives | The page does not follow the house page structure. | Add the note and the handoff sentence. Add a Deep dives section (the `adk run` item above can go there). | done |

### tutorial/part-1/1.4-cloud-run.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F044 | Whole page | The page runs 812 words against a 750 limit | The house limit is 750 words per page. | Trim the deploy-script deep dive. | done |
| F045 | 95, 101 and 128 | Deep-dive headings are statements ("### Why a Job and not a service") | House style writes deep-dive headings as questions. | Rename them as questions, for example "### Why a Job and not a service?". | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F046 | 71 | "The INFO execution shows the five-line lifecycle from 1.1.1." | The block shows three lines, ordered Sending, tool, Response, while 1.1.1 shows Sending, Response, tool. The rerun on jwd-dev-1 also logged two `httpx` request lines and `Closing runner…` / `Runner closed.`, and the lines were not batched. | "The INFO execution carries the lifecycle lines from 1.1.1 (trimmed)" | done |
| F047 | 148 | No teardown step | The page creates the Cloud Run Job `adk-logging-job` and never deletes it. | Add "**Step N — Tear down.**" with `gcloud run jobs delete adk-logging-job`, one flag per line. | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F048 | 74–76 | "The Cloud Run docs … say a line written to stderr is recorded as ERROR." | No docs page is cited. The only source found is ADK's own comment at `google/adk/models/lite_llm.py:3002`, which says "GCP". | Cite the docs URL, or write "ADK's own source comment (`lite_llm.py:3002`) says…". | done |
| F049 | 88–91 | "Cloud Run batches burst console output…" | No source is given, and the rerun on jwd-dev-1 showed lines were not batched. It is a caveat, not orientation, so it distracts from the step. | Delete the NOTE, or move it to a deep dive with a source. | done |
| F050 | 15–16 and 82–83 | "the answer is not what the common advice says" and "two-thirds of the way" | Neither phrase states the finding. | "Cloud Run files plain stderr lines as Default severity, not ERROR" and "Deploying with no logging changes still delivers your logs, and `LOG_LEVEL` still controls which ones appear." | done |

### tutorial/part-1/1.5-http-server.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F051 | 31 | "SERVICE=adk-logging-api-warn LOG_LEVEL=warning ./deploy/deploy_api.sh" | House style does not use inline environment prefixes. | Replace the inline prefixes with `export SERVICE=…`, `export LOG_LEVEL=warning`, the script call, then `unset SERVICE LOG_LEVEL`. | done |
| F052 | Whole page | The page runs 752 words | The house limit is 750 words per page. | Trim to 750 words or fewer. | done |
| F053 | 114 | "### How the server is composed" | House style writes deep-dive headings as questions. | "### How is the server composed?" | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F054 | 16, 63 and 100 | "Four sources interleave in the INFO service" and "all of Part 1's streams in one place" | The four loggers are three streams. `agent.server` and `demo_agent.agent` are both stream 1 (your code). Stream 4 (OpenTelemetry) is Part 5. | "Three streams interleave: your code (`agent.server`, `demo_agent.agent`), `google_adk`, and uvicorn's access line. Stream 4 is Part 5." | done |
| F055 | 100 | "Four sources interleave in the INFO service" | The rerun on jwd-dev-1 also shows `INFO - httpx - HTTP Request: POST https://aiplatform.googleapis.com/…` twice per request. It comes from a library outside `google_adk`. | Name the `httpx` lines, and say they show that the root log level also reaches third-party libraries. | not applicable (with the `==2.8.0` pin, the 2026-10-02 rerun on jwd-gcp-demos logged no `httpx` lines) |
| F056 | 152 | "`GET /healthz` for the readiness probe" | `deploy_api.sh` configures no probe, and Cloud Run's default startup probe only checks the TCP port. | "`GET /healthz`, a conventional health endpoint; Cloud Run's default probe only checks that the port is open." | done |
| F057 | 120–121 | "the module calls the same `configure(level)` as 1.1" | 1.1 never shows a `configure()`. `09_min_api.py:41-53` adds a `getattr` default and a root `setLevel`. | "makes the same two calls as 1.1 (`basicConfig` and `setLevel` on `google_adk`), plus a root `setLevel`." | done |
| F058 | 166 | No teardown step | The page deploys `adk-logging-api` and `adk-logging-api-warn` and never deletes them. | Add a teardown step that deletes both services. | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F059 | 93–97 | The WARNING block, with a bare `WARNING` row and a `favicon.ico` 404 | The page never explains either row. | Add "(the favicon 404 comes from opening the URL in a browser)", or recapture the output. | done |

### tutorial/part-1/1.6-agent-runtime.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F060 | 212 | "about ninety lines" | `agent_runtime_byoc/main.py` has 107 lines. | "about a hundred lines" | done |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F061 | 146 | "**Expected output** — your logs in **your** format:" | House style allows an em dash only in a Step label, and does not bold ordinary words. | "**Expected output** (BYOC, your format):". Remove the bold from "**your**". | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F062 | Whole page | "It deploys by one of two telemetry routes… `ENABLE_VIA_ENV=1`…" (line 237 onward) | The page runs 1,748 words against a 750 limit. It covers two deploys, two ways of querying them, two script walkthroughs, and a passage on turning on telemetry that Part 6 covers. | Split the native deploy and the BYOC deploy into 1.6 and 1.7. Replace the telemetry passage with "Part 6 covers telemetry." | done (split into 1.6 native and 1.7 BYOC) |
| F063 | 323–325 | "the same `stream_query` SDK call … fails on a BYOC handle with `AttributeError`" | `agent_runtime_byoc/deploy_byoc.py:28-46` registers `stream_query` and `async_stream_query` in `class_methods`, and the SDK builds handle methods from them (`_register_api_methods` in `vertexai/_genai/agent_engines.py`). The rerun on jwd-dev-1 used the page's curl path, so it did not exercise this. | Show the captured error, or write "This tutorial queries BYOC through the `/api` passthrough." | done |
| F064 | 187 | "`adk deploy agent_engine` **creates a new reasoning engine on every deploy**" | That happens only when `--agent_engine_id` is not passed. | "…on every deploy unless you pass `--agent_engine_id`." | done |
| F065 | 200 | "The deploy command has no env flag" | `--env_file` exists but is deprecated in 2.8.0. | "Its `--env_file` flag is deprecated, so it reads the agent folder's `.env`." | done |
| F066 | 245 | `--otel_to_cloud \                 # ENABLE_VIA_ENV=1 drops this…` | A `#` comment after a `\` continuation stops the shell from continuing the command. | Move the comments into prose and put one flag per line. | done |
| F067 | 114 | "Your `basicConfig` format did not take." | On a native deploy the agent calls `basicConfig` only when `LOG_LEVEL` is set, so this blames the wrong thing. | "The platform, not your code, sets the format here." | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F068 | 189–190 | "Delete old engines when you are done; both deploy scripts print teardown commands." | Teardown is mentioned but not given. The reader must find the commands in script output. | Add a teardown step with the delete commands. | done |
| F069 | 105–111, 148–154 and 261–269 | The two log tables for the native and BYOC deploys, and the BYOC setup traps list | On jwd-dev-1, neither engine's logs appeared under `resource.type="aiplatform.googleapis.com/ReasoningEngine"` in about 10 minutes, although both answered. The same filter returns September data in jwd-gcp-demos, so the cause is likely the project, but the page's two log tables could not be rechecked. The first BYOC registration also failed with "failed to start and cannot serve traffic", not the documented `FAILED_PRECONDITION`, and an unchanged rerun succeeded. | Add to the list of BYOC deploy problems: "On a fresh project the first registration can fail while new IAM grants propagate; rerun the script." | done (both engines' logs read back on jwd-gcp-demos; propagation trap added to 1.7) |
| F070 | 73 and 120 | "**Test the native deploy (terminal 1).**" and "**Test the BYOC deploy (terminal 2).**" | House style uses `**Step N — …**` labels, and each command fence needs a **Command:** label. These have neither. | Rewrite as Step labels and add **Command:** before each fence. | done |
| F071 | 336–337 | "`agentplatform.Client` is the current name for what used to be `vertexai.Client`" | The code uses `vertexai.Client`, so the reader cannot tell which to use. | "The code uses `vertexai.Client`, which still works but warns; `agentplatform.Client` is its new name." | done |
| F072 | 108 | "agent.py:53" | The current code logs at `demo_agent/agent.py:54` (see 1.3). | Recapture the native output. | done |
| F073 | 186–190 | The WARNING callout, three sentences | House style allows one sentence in a WARNING callout. | "> `adk deploy agent_engine` can exit 0 when the deploy failed, so confirm with the query." | done |

### tutorial/part-2/index.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F074 | 27 | "**The flag worked. It does not reach this stream.**" | House style does not use bold for body sentences. | "The flag worked, but it does not reach this stream." Drop the bold. | done |
| F075 | 67 of tutorial/how-to-choose.md | The Date cell is empty in the how-to-choose run row matching this page | The captured lines on this page are dated 2026-08-31. | Fill it in with 2026-08-31. | still real (date goes in with the how-to-choose fixes) |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F076 | 19 | `CLI -->\|"setLevel()"\| S1["1 · your code"]` | The diagram shows `setLevel()` on the wrong stream. `setup_adk_logger` calls `logging.basicConfig(level=…)` on the root logger, which stream 1 inherits. It calls `setLevel` only on `google_adk`. | Label the stream 1 edge "root level" and keep "setLevel()" on the stream 2 edge. | done |
| F077 | 32 | "The fix, when you run your own server, is to hand uvicorn a logging config with a filter" | The reader just ran `adk api_server` in 1.3 and gets no answer for that case. | "`adk web` and `adk api_server` start uvicorn for you with its default config, so they give you no place to add the filter. Part 4 builds a server where you can." | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F078 | 77–79 | "That is the move the rest of this tutorial builds on: …" | "The move" does not say what it is, and the page ends without the handoff sentence house style requires. | Replace the sentence with "Part 3 turns to stream 2 and the two ADK plugins that narrate each step." | done |
| F079 | 52–72 | The `02_tame_uvicorn.py` fence has no expected output | The four `curl` calls' client-side output is not described either. | Add "The `curl` calls print each response; the server terminal shows the access log." | done |

### tutorial/part-3/index.md

No findings.

### tutorial/part-3/3.1-loggingplugin.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F080 | 112–116 | "`BasePlugin` declares fourteen async callbacks (… three error hooks, and `close`)" | The callback and error-hook counts are off. `base_plugin.py:114-394` declares fifteen callbacks, with four error hooks: `on_model_error_callback`, `on_tool_error_callback`, `on_agent_error_callback`, and `on_run_error_callback`. | "fifteen async callbacks (… four error hooks for the model, tool, agent, and run, and `close`)" | done |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F081 | 110 and 153, linked at 29–30 | "How plugin hooks fire", "What LoggingPlugin fixes in source" | House style writes deep-dive headings as questions. | Rename both headings to questions, such as "How do plugin hooks fire?". Update the anchors that link to them. | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F082 | 40–44 and 151 | "29 lines" and "lightly trimmed" | The sample output is far shorter than the real run. The rerun on jwd-dev-2 printed 64 plugin lines for one question, in the same hook order. The page's output is much more than lightly trimmed. | "64 lines for one question; trimmed here to one of each kind." | done |
| F083 | 169 | "Text and system-instruction length \| truncated at 200 characters \| `_format_content`" | The table credits the wrong function for system-instruction truncation. `_format_content` truncates only message text. The system instruction is cut by `[:200]` in `before_model_callback`. | Split the row in two, and name `before_model_callback` on the system-instruction row. | done |
| F084 | 11 | No **Why you are here.** note | House style requires that note on every page. The page runs 865 words against a 750-word limit, and the first **Command:** arrives about ten sentences in. | Add "> **Why you are here.** INFO says little about tool calls. `LoggingPlugin` prints every step of one question to your terminal." Then trim the deep-dive source excerpts to one. | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F085 | 100–106 | "**The catch that decides where you use it.**" | The WARNING callout is six sentences long. House style allows one. | Replace it with "> **Use it locally only.** It writes with `print()` and terminal color codes, so it ignores your log levels and garbles Cloud Logging." Move the rest into the body. | done |
| F086 | 27–28 | "neither `--log_level` nor a `dictConfig` can reach it." | "a `dictConfig`" does not say why the plugin is unreachable. The plugin's lines are plain stdout, outside all four log streams, so no logging config touches them. | "neither `--log_level` nor your own logging config can reach it: these are plain stdout lines, outside the four log streams." | done |
| F087 | 23–24 | "Read this section for how a plugin works as much as for what this one prints." | It promises a benefit the section's own heading already delivers. | Delete the sentence. | done |

### tutorial/part-3/3.2-loggingplugin-cloud-run.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F088 | 19–21 | "Example 03 configures no logging of its own, so `LOG_LEVEL` controls only the framework (stream 2), never the plugin." | `LOG_LEVEL` also controls your tool's own lines. `demo_agent/agent.py:29-33` applies `LOG_LEVEL` to the root logger too, so it also silences the tool's own `tool get_weather called` line (stream 1, your code's loggers). | "Example 03 configures no logging, but `demo_agent` applies `LOG_LEVEL` to the root and `google_adk` loggers, so it controls your tool's lines (stream 1) and the framework (stream 2), never the plugin." | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F089 | 81–82 | "**Expected output** — the full narration for both runs" | The output is two lines, not the full narration. It comes from a `--limit=10` read. The rerun on jwd-dev-2 returned the 10 newest lines of the WARNING run, and each run emits 64 plugin lines. | "**Expected output** (newest first, trimmed to two): plugin lines with blank severity and the terminal color codes in the payload" | done |
| F090 | 37 | "Two reads, each isolating one stream by a substring of its lines." | The first read does not isolate one stream. `textPayload:"logging_plugin"` also matches the framework's "Plugin 'logging_plugin' registered." line (`plugin_manager.py:121`). | "Two reads, each selecting lines by a substring. The first also catches the framework's 'Plugin registered' line." | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F091 | 29 and 102 | "SCRIPT=examples/03_logging_plugin.py ./deploy/deploy_plugin_job.sh" | House style forbids inline env prefixes: export the variable, then run the script. The teardown also puts its flags on one line, and nothing says what the script does. | Use `export SCRIPT=examples/03_logging_plugin.py`, then the script, then `unset SCRIPT`. Put one flag per line in the teardown. Add "The script deploys the Job and runs it once at INFO." | done |
| F092 | 12 | "> [!TIP] **Optional. Why you are here.**" | The opening callout uses the wrong type. House style calls for a NOTE here, not a TIP. | Change `> [!TIP]` to `> [!NOTE]`. | done |
| F093 | 93 | "(The `google_adk` lines have 1.4's problem: on stderr, still Default.)" | "1.4's problem" is not spelled out. A reader has to remember 1.4 to decode "problem". | "(The `google_adk` lines also land with Default severity, as in 1.4.)" | done |

### tutorial/part-3/3.3-debugloggingplugin.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F094 | 25 | "**👉 Do this**, then open the file it writes." | House style ends the Do this label with a period and puts the instruction after it. | "**👉 Do this.**" | done |
| F095 | 75 | The deep-dive heading "How it differs from LoggingPlugin in source" | House style writes deep-dive headings as questions, and this one is a statement. | Rename it to a question. | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F096 | 54–58 | No mention that the user message is missing from the entry sequence | The file has no user-message entry, and the page never says so. `on_user_message_callback` runs before `before_run_callback` (`runners.py:677` vs `:695`). The plugin therefore drops the `user_message` entry and logs `No debug state for invocation …, skipping entry` on every run. | Add "Unlike `LoggingPlugin`, the file has no user-message entry; the prompt appears inside the first `llm_request`." | done |
| F097 | 38–52 | "**Expected output** — one YAML document for the invocation, a list of timestamped entries:" | The excerpt hides the document's header and per-entry fields. The real document is a mapping with `invocation_id`, `session_id`, `app_name`, `user_id`, `start_time`, then `entries:`. Each entry also carries `invocation_id` and `agent_name`. The excerpt drops these without saying so. The rerun on jwd-dev-2 confirmed the header, 14 entries, and no `user_message`. | Change the label to "one YAML document per invocation: a header, then an `entries:` list. First entry, trimmed:", and show the real fields. | done |
| F098 | 38 | "one YAML document" | The file holds one document per run, not one in total. The plugin opens the file with `O_APPEND` and writes `---` per invocation, so `cat` shows every earlier run. The rerun on jwd-dev-2 saw the existing file go from 4 to 5 documents. | Add "Each run appends a `---` document; delete the file first for a clean view." | done |
| F099 | 49 | "- text: What's the weather in a city you don't know, like Paris?" | The question changes from London to Paris with no explanation. Part 3 uses the London question everywhere else. | Add "Example 04 asks about a city the tool does not know, so the file includes an error path." Or switch the question to London. | done (kept Paris and said why: the file then includes the error path) |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F100 | 65 | "credential models, secret-named keys, private-key blocks, and **all** `temp:` state" | "credential models", "secret-named keys", and `temp:` state are not explained. | "credential objects, keys with secret-like names, private-key blocks, and every `temp:` state key (ADK's per-question scratch state)" | done |

### tutorial/part-3/3.4-debugloggingplugin-cloud-run.md

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F101 | 51–54 | "have the script `cat` the file to stdout at the end. It lands in Cloud Logging as one large text payload" | Stdout lands as one entry per line, not one payload. Cloud Run splits plain stdout on newlines, so the YAML lands as one entry per line. | "It lands in Cloud Logging as one entry per line, which you would have to stitch back together." | done |
| F102 | 31–32 and 61 | No mention that the script creates a bucket, and no step that deletes it | The teardown leaves the bucket and file behind. `deploy_plugin_job.sh` creates `gs://$BUCKET` if missing, which the page never says. The teardown deletes only the Job, so the bucket and `adk_debug.yaml` remain. | Add "The script creates `gs://$BUCKET` if it does not exist," and add `gcloud storage rm --recursive "gs://$BUCKET"` to the teardown. | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F103 | 27 | "MOUNT=1 SCRIPT=examples/04_debug_plugin.py ./deploy/deploy_plugin_job.sh" | House style forbids inline env prefixes. `$BUCKET` is never set on this page: it comes from `env.sh`, which only 3.2 sources. | Use `source env.sh`, `export MOUNT=1`, `export SCRIPT=examples/04_debug_plugin.py`, the script, then `unset MOUNT SCRIPT`. | done |
| F104 | 34–36 | "Cloud Logging has one more line, the plugin's own warning about the file it wrote:" | No command shows how to read the plugin's warning. The rerun on jwd-dev-2 found two plugin warnings in Cloud Logging: the file-mode one and `No debug state for invocation …, skipping entry`. | Add a `gcloud logging read` **Command:** before the output, and mention both warnings. | done |
| F105 | 44, 46 and 53 | "bucket IAM is your new `0600`", "'file, not stream' property", "Cloud Storage FUSE mount" | Each phrase is Unix or storage shorthand a reader has to decode. | "access to the bucket now protects the file", "the one-file-per-run property", and "the Cloud Storage volume mount" | done |
| F106 | 13–14 | "You would not run it on Cloud Run in practice" | This page and 3.5 disagree about Cloud Run. 3.5 says "From a Cloud Run Job, use the mounted bucket from 3.4." The two pages give opposite advice. | Reword one so both say the same thing. Suggest keeping 3.4's mounted-bucket advice and softening this sentence. | done (3.4 now frames the run as a lesson, not as advice against Cloud Run) |

### tutorial/part-3/3.5-plugin-or-level.md

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F107 | 41–43 | "DEBUG shows the framework's own internals (the wire-level request, HTTP retries, session-service work), none of which have plugin hooks." | Plugins can see the wire-level request. It passes through `before_model_callback`, and `DebugLoggingPlugin` captures it in full (3.3). | "DEBUG shows internals plugins cannot see: HTTP retries and session-service work." | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F108 | 24 | "3.2 proved it: WARNING silenced the framework and the narration kept going" | WARNING silenced more than the framework. It also silenced the tool's own line (stream 1), as 3.2 shows. | "WARNING silenced the `logging` lines and the narration kept going." | done |
| F109 | 26 and 56 | "You own the sink" and no handoff sentence to Part 4 | House style requires a closing sentence that introduces the next page. "Sink" is jargon for where output goes. | Add "Part 4 builds the structured plugin that works wherever you deploy," and change "You own the sink" to "You choose where the output goes." | done |

### tutorial/part-4/index.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F110 | 13–17 | "**Why you are here.**" note, "Part 3's visibility", "owns every stream" | House style keeps the note to two sentences. This one runs three and uses two phrases the reader has to decode. | Cut the note to two sentences and drop both phrases: "**Why you are here.** `LoggingPlugin` prints and DEBUG is plain text, so neither gives a running service logs you can query and alert on. This part builds a plugin that emits JSON records and runs it in your own server on Cloud Run." | done |

### tutorial/part-4/4.1-structured-plugin.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F111 | 39–45 | The **Expected output** block, three lines with no `"logger"` or `"event"` key | `JsonFormatter` always writes `"logger"` (`examples/05_structured_plugin.py:155`) and passes `event` through, and `before_model_callback` emits `llm_request` lines the block leaves out. The rerun on jwd-dev-3 showed six lines per question, each with `logger` and `event`. | Recapture the output. Or label the block "(trimmed)" and show the real keys, for example `{"severity": "INFO", "message": "llm_response", "logger": "agent.telemetry", "event": "llm_response", …}`. | done |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F112 | 1 and 3, 61 and 63 | Prev and Up both link to `index.md` | Two nav links point to the same page, which is redundant. | Relabel Prev "← Part 4 · Structured logging" and drop the duplicate, or keep both if the template allows. Low priority. | not applicable (the subtask template links Prev to the part landing page from a part's first page) |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F113 | 31 and 43 | "asks *"What's the weather in New York?"*" | The example asks about New York, but pages 4.2 and 4.3 both use Tokyo. The prompt comes from `examples/05_structured_plugin.py:180`. | Change the example prompt to Tokyo and recapture the output. | done (example 05 now asks the Tokyo question) |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F114 | 11 and 57 | No **Why you are here.** note, no closing handoff | The page opens straight into code. House style gives every page a short note on why the reader is here, and a line pointing to the next page. | Add "> **Why you are here.** `LoggingPlugin` prints text. To query and alert on events, write your own plugin that emits JSON `logging` records." at the top, and end with "4.2 runs this plugin inside a real HTTP server." | done |
| F115 | 54–57 | "One detail the example teaches by doing… This bites everyone once." | The gotcha is the key name `tool_args` versus `args`. It is told in informal shorthand, interrupts the main steps and gives no reason. | Move it to `## Deep dives` under the question "Why is the key `tool_args`, not `args`?" | done |

### tutorial/part-4/4.2-custom-server.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F116 | 8, 14 and 59 | "All four streams under one config" (the What it means callout), and "owns all four streams" in the title, intro, and Part 4 subtitle (`index.md` lines 9 and 24) | The page claims the server configures four streams, but it configures three. Nothing in `06_custom_server.py` configures OpenTelemetry (stream 4), and the captured output shows only streams 1 and 2. | Replace the callout with "Your code, the framework, and uvicorn share one config (streams 1–3). Stream 4 is Part 5." Change "all four streams" to match in the title, intro, and subtitle. | done |
| F117 | 88–89 | "The `dictConfig` at startup covers your telemetry logger, the `google_adk` level, the root handler, and the `uvicorn.access` filter from Part 2." | The page names a `uvicorn.access` filter the config does not have. `configure_logging()` in `examples/06_custom_server.py` sets up no `uvicorn.access` logger or filter. `log_config=None` (line 251) sends access lines to the root JSON handler unfiltered. | Change to "…covers your telemetry logger, the `google_adk` level, and the root handler. With `log_config=None`, uvicorn's access lines reach that root handler as JSON." | done |
| F118 | 115–116 | "Logs Explorer groups every line of one request, across all four streams." | Access lines are logged after `current_trace.reset`, so they carry no trace field. The rerun on jwd-dev-3 confirmed this. OpenTelemetry output does not pass through this formatter at all. | Change to "groups every line written while the request runs: your code, the plugin, and `google_adk`." | done |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F119 | 46, 61 and 133 | "**and**", "**not**", "**every**" | House style does not use bold for emphasis inside sentences. | Remove the bold. | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F120 | 132 and 153 | The sequence diagram's "middleware" participant, and "The server parses it once at the start of each request". | The diagram shows middleware that does not exist. The server has no middleware. The `/chat` handler sets the context variable that carries the trace id. | Rename the participant "/chat handler" and reword the sentence to say the handler parses it. | done |
| F121 | 19–20 | "its formatter writes two fields Cloud Logging understands" | The formatter writes three fields. `CloudRunJsonFormatter` also writes `logging.googleapis.com/sourceLocation` (`examples/06_custom_server.py:102-106`). Neither the snippet nor the output shows it. | Name the third field. Or say the snippet and output are trimmed. | done |
| F122 | 90–103 | The `TruncateFilter` block in the deep dive | The deep dive is about severity and trace fields, and this block is unrelated to both. | Replace the block with one sentence: "The same config attaches a filter that truncates long DEBUG lines." | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F123 | 43 | `-d '{"message":"weather in Tokyo?"}'` | The curl prompt is not the question the rest of Part 4 asks. Other pages ask "What's the weather in Tokyo?", so output may not match. | Change to `-d '{"message":"What'\''s the weather in Tokyo?"}'`. | done |
| F124 | 69, 105 and 130 | "The server shape", "The two fields the formatter writes", "How the trace reaches framework logs" | Deep-dive headings are labels, not questions. House style words them as questions the reader would ask. | Rename to "What does the server look like?", "Which two fields does the formatter write?", and "How does the trace reach framework logs?" Then update every link to those anchors (lines 22–23 and 63–64). | done |
| F125 | 71 | "Built on ADK 2.x idioms." | The phrase names no idiom, so the reader cannot tell what to look for. | Replace with "The server builds an `App` with your plugin, hands it to a `Runner`, and closes the runner on shutdown." | done |

### tutorial/part-4/4.3-server-cloud-run.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F126 | 49–60 | The **Expected output** table for the `jsonPayload.message:*` read | The table does not match a real run. The rerun on jwd-dev-3 returned 8 rows per question, not 6, because a question that uses the tool calls the model twice, so `llm_request` and `llm_response` each appear twice. Rows came newest first, the reverse of the page's order. Two uvicorn startup lines (`Started server process [1]`, `Uvicorn running on…`) also matched, because their `color_message` extra keeps them in `jsonPayload`. | Recapture with `--order=asc`, show 8 rows per question, and add `jsonPayload.event:*` to the filter to drop the startup lines. | done (filter is `jsonPayload.message:* trace:*` with `--order=asc`; the review's `jsonPayload.event:*` would also drop the two `chat_request_*` rows, so it shows 6 rows, not 8) |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F127 | 89 | "`jsonPayload.latency_ms` a metric you can chart" | Charting a log field needs a log-based metric, so the field is not a metric by itself. | Change to "a field you can turn into a log-based metric". | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F128 | 65–66 | "The framework and Uvicorn lines are still there, as plain `textPayload`." | This was observed, but page 4.2 shows the same lines as JSON, so the pages seem to contradict each other, and no reason is given. The server writes them as JSON with three fields: `message`, `logging.googleapis.com/trace`, and `logging.googleapis.com/sourceLocation`. Cloud Logging moves the last two into the log entry's own fields, and a payload left with only `message` is stored as plain text. | Add "Cloud Logging moves the trace and source-location fields out of each JSON line into the log entry. A line left with only `message` is stored as `textPayload`, so the framework lines land there even though the server wrote them as JSON." | done |
| F129 | 90–92 | "shows the whole request's lifecycle grouped, framework and access lines included." | The page says framework and access lines are grouped by request. The rerun on jwd-dev-3 showed the container's access line has no trace, because uvicorn writes it after the handler clears the trace id. Only Cloud Run's own `run.googleapis.com/requests` entry is grouped with the rest. | Change to "…grouped: your lines, the plugin's events, the `google_adk` lines, and Cloud Run's own request entry." | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F130 | 94–100 | "**Your model's region is not your service's region.**" | The WARNING callout runs five sentences. House style allows one sentence in a WARNING callout, and this one buries the action. | Replace with "> **Set `GOOGLE_CLOUD_LOCATION` as a real Cloud Run env var.** Without it, a deploy can succeed while every `/chat` returns 500." Move the rest to a `## Deep dives` question. | done |
| F131 | 32–47 | One fence holding `URL=$(gcloud …)`, a `curl` with `-s -X -H` on one line, and `gcloud logging read` | One code block mixes three jobs and a crowded curl line, so the reader cannot tell where one step ends. House style puts one action per block and one flag per line. | Split into three steps. Use `export URL=$(gcloud …)` in the first, and put each curl flag on its own line. | done |
| F132 | 108 | No closing handoff to 4.4 | House style ends each page with a line pointing to the next. | Add "4.4 compares a per-agent callback with this plugin." | done |

### tutorial/part-4/4.4-callback-or-plugin.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F133 | 51–53 | "in Cloud Logging you can filter to `agent.telemetry` and see your events without the framework's." | The page says you can filter Cloud Logging by `agent.telemetry`, but that field is not shipped. `CloudRunJsonFormatter` leaves out `record.name` because `name` is in `_RESERVED` (`examples/06_custom_server.py:96`), so the JSON has no logger field. The rerun on jwd-dev-3 returned 0 entries for `jsonPayload.logger="agent.telemetry"`. | Change to "…add `entry["logger"] = record.name` to your formatter, then filter on `jsonPayload.logger="agent.telemetry"`." | done |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F134 | 63 | "downstream BigQuery or Looker analysis" | The page never introduces those tools. | Change to "one field schema for every agent". | done |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F135 | 23–24 | "A level on `google_adk` answers the first for free: requests sent, responses received, retries, errors." | This overstates what a `google_adk` level shows. At INFO, ADK logs only "Sending out request". The response log is DEBUG only (`google_llm.py`, `_build_response_log`). Retries are logged by `google_genai`, outside the `google_adk` loggers. | Change to "A `google_adk` level shows requests and errors at INFO, and request and response bodies at DEBUG. Retry lines come from the separate `google_genai` logger." | done |
| F136 | 70 | "Both run in the request thread" | Plugin and agent callbacks run on the asyncio event loop, and a `StreamHandler` writes synchronously, so slow work blocks every request. | Change to "Both run on the event loop, so keep the work cheap and non-blocking." | done |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F137 | 76 | No step to run, no closing handoff | Every other page in Part 4 has something to run, and ends by pointing to the next page. | Add a step that attaches `log_tool` to the demo agent and shows one captured line. Or treat the page as reference and end with "Part 5 adds stream 4, OpenTelemetry." | done (kept as a reference page; ends with the Part 5 handoff) |
| F138 | 27, 51–52, 67 and 69–70 | "the callback-or-plugin job", "siloed by design", "the name rides on every record", "turns the hook into a guardrail" | Each phrase compresses an idea the reader must decode. | Replace with "what a callback or plugin is for", "scoped to one agent", "the logger name is on every record", and "so the hook can block or replace the step". | done |
| F139 | 73–76 | "**The takeaway.** …" | House style does not allow a closing summary of what the page just said. | Delete the takeaway. | done |

### tutorial/part-5/index.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F140 | 13–16 | The "Why you are here" note | The note runs longer than one sentence. House style allows one. | Cut it to one sentence. | still real |
| F141 | 16 | "adds **export**, not tracing" | House style does not use bold for emphasis. | Remove the bold from "export". | still real |
| F142 | 23, 24, 27, 28 and 29 | The table titles for 5.1, 5.2, 5.5, 5.6 and 5.7 | They differ from each page's H1 and nav label, so one page has two titles. | Make them match, so every page has one title. | still real |

### tutorial/part-5/5.0-what-stream-4-is.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F143 | 48–49 | "every trace in this part reads itself" | The phrase is figurative and gives the reader nothing to act on. | "The traces in this part use only these." | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F144 | 13–14 | "all produced by ADK itself with no extra packages" | This holds only when nothing is configured. With `--otel_to_cloud` and `google-adk[otel-gcp]` installed, a separate library, `opentelemetry-instrumentation-google-genai`, produces the `generate_content` span, the `gen_ai.*` events and the token metrics instead of ADK (ADK checks this in `_should_emit_native_telemetry`). The 5.2 deep dive says so, so the two pages disagree. | Add "With `--otel_to_cloud` and `google-adk[otel-gcp]`, the `opentelemetry-instrumentation-google-genai` library produces the `generate_content` span and the events instead (5.2)." | still real |
| F145 | 8 | "# 5.0 · What stream 4 is" | Part 5 is the only part numbered from N.0. 5.0 is a concept page with no "Why you are here" note, no step and no command. Every other part starts at N.1. | Fold 5.0 into `part-5/index.md` and start numbering at 5.1. Or give 5.0 the standard subtask layout and record the N.0 convention in the tutorial's `CLAUDE.md`. | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F146 | 12–14 | No definition of OpenTelemetry, OTel, span, trace or OTLP | This is where the reader first meets all five terms, and none is explained. | Add "Stream 4 is OpenTelemetry (OTel), a separate telemetry SDK. A span is one timed operation; a trace is the tree of spans for one question." | still real |
| F147 | 12 | "Streams 1-3 are Python `logging`" | The reader has to look back to learn which streams these are. | "Streams 1-3 (your code, `google_adk`, `uvicorn.access`) are Python `logging`." | still real |

### tutorial/part-5/5.1-adk-web-already-tracing.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F148 | Whole page | The page runs 852 words | It is over the 750-word limit. | Cut to the 750-word limit. | still real |
| F149 | 13–16 | "a short list of deltas" | The "Why you are here" note runs three sentences. House style allows one. | Cut the note to one sentence. | still real |
| F150 | 84 and 104 | "Where these spans have been living"; "The endpoint behind the tab" | House style writes deep-dive headings as questions. | Rename both to questions. | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F151 | 26–27 | "Go to `localhost:8000`, pick **demo_agent** from the app dropdown, start a new session or reuse one, and ask:" | Four separate actions share one sentence, which is hard to follow while clicking. | Split it into one bullet per action. | still real |
| F152 | 71 | "the join key back to the `/run` response's event list" | Nothing on this page calls `/run`, so the reader has no response to compare against. | "it matches the event ids in an `adk api_server` `/run` response (1.3)." | still real |

### tutorial/part-5/5.2-otel-to-cloud.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F153 | 181–183 | "If they hold the prompt and reply, `=true` turned content on in both streams, and Step 3 turns the span side off. If they are already empty, Step 3 has nothing to turn off." | The page says the spans may be empty of prompt and reply text. `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS` defaults to on (`google/adk/telemetry/context.py:107-113`), so the spans carry the prompt and reply from Step 1 on, whatever `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` says. The rerun on jwd-dev-4 showed full text in a clean copy, but empty spans (`{}`) in the working tree, because the gitignored `demo_agent/.env` sets `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`. | Replace both sentences with "The spans hold the prompt and reply, and did in Step 1 too: `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS` defaults to on and does not depend on the event setting. Step 3 turns it off." Also add to Step 1's "What you are looking at" (line 114): "`<elided>` applies to the log events only, not the spans." | still real |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F154 | Whole page | The page runs 2,024 words | It is 2.7 times the word limit, and about 1,000 words are deep dives. | Cut toward the limit. | still real |
| F155 | 119–312 | Steps 2 to 5, which cover the content settings | They make one page do two jobs: the flag, and the content settings. | Move them to their own page. | still real |
| F156 | 318–425 | Deep dives on IAM roles, the metrics 400 error and `.env` | They are reference material that lengthens a tutorial page. | Move them to how-to-choose or 5.6. | still real |
| F157 | 57, 132, 221 and 279 | The London prompt fence appears four times | Repeating the same fence adds length and nothing new. | Show it once, then say "Ask the London question in a new session." | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F158 | 20–21 | "The flag authenticates with Application Default Credentials (ADC), not a key file or `GOOGLE_API_KEY`." | A key file named by `GOOGLE_APPLICATION_CREDENTIALS` is itself a form of ADC, so the contrast is false. | "…with Application Default Credentials (ADC), not `GOOGLE_API_KEY`." | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F159 | 206 and 213 | "semantic convention" and `gen_ai_latest_experimental` (Step 4) | Step 4 uses both terms without defining them. The reader cannot tell what the two formats are or how they differ. | Add "A semantic convention is OpenTelemetry's naming scheme for GenAI telemetry. The default format writes separate `gen_ai.system.message`, `gen_ai.user.message`, and `gen_ai.choice` events; the experimental one writes one `gen_ai.client.inference.operation.details` event per model call." | still real |
| F160 | 442 | No cleanup step at the end of the page | Exports from Steps 1 to 5 stay set in the shell. `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`, `OTEL_SEMCONV_STABILITY_OPT_IN` and the `EVENT_ONLY` event content setting are all still exported when the reader starts 5.3. The rerun on jwd-dev-4 confirmed this. | End the page with `unset` lines for all four variables. Or add "Close this terminal before 5.3." | still real |
| F161 | 17, 64 and 178 | "**Before you start, once.**", "**Read the turn back.**" and "Now check the spans." | These are steps but lack the `**Step N — …**` label, and the prerequisite commands sit as inline code in a list with no command fence. | Make each one a numbered Step with a **Command:** fence, and have 5.3 and 5.4 link back to them. | still real |
| F162 | 67, 64–65 and 178–179; 5.4 lines 66–69 | **Command:** followed by the query `logName=~"gen_ai\."` | It is a query typed into a browser, not a command. The Logs Explorer and Trace Explorer directions are also prose, not bullets. 5.4 has the same problem. | Label it "**Query:**" and write the Logs Explorer and Trace Explorer directions as bullets, here and in 5.4. | still real |

### tutorial/part-5/5.3-api-server.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F163 | 55–61 | `curl -s -X POST localhost:8000/apps/demo_agent/users/u1/sessions/s5-api \` and the `/run` call | Several flags share one line, which is hard to scan. | Put each flag on its own line. | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F164 | 65–69 | "The entries match 5.2 Step 4…" | The page shows no output block, and how-to-choose says this run was not repeated, but the page does not say so. The rerun on jwd-dev-4 confirmed there is nothing to compare against. | Capture the output and show it. Or add "Not re-run in this sequence; see Not verified in how-to-choose." | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F165 | 64–65 | "terminal 1 prints the same five INFO lines as 5.1" | 5.1 never shows those lines. 5.2 does. | Change "5.1" to "5.2". | still real |
| F166 | 53 | `START=$(date -u +%Y-%m-%dT%H:%M:%SZ)` | Nothing later reads `START`, so the reader wonders what it is for. | Delete the line. | still real |

### tutorial/part-5/5.4-cloud-run.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F167 | 75–76 | "The same events appear, one `gen_ai.client.inference.operation.details` per `call_llm`" | The deploy does not set `OTEL_SEMCONV_STABILITY_OPT_IN`, so the events come in the default format: separate `gen_ai.system.message`, `gen_ai.user.message`, and `gen_ai.choice` events (`opentelemetry/instrumentation/google_genai/generate_content.py:1017`). The rerun on jwd-dev-4 showed eight events in that format and none named `operation.details`. | "The same `gen_ai.system.message`, `gen_ai.user.message`, and `gen_ai.choice` events as 5.2 Step 1 appear, now from Cloud Run. To get one `operation.details` event per model call instead, add `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` to `--set-env-vars`." | still real |
| F168 | 76–78 | "Content is off (`<elided>`) because `demo_agent/.env`'s `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` shipped inside the image." | That variable controls content on spans only, as 5.6 itself says. Content in the log events is off because `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` is `NO_CONTENT`, which is also its default. | "Event content is elided because `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` defaults to `NO_CONTENT`. Span content is controlled separately by `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS`, which defaults to on; `adk deploy cloud_run` does not turn it off." | still real |
| F169 | 109–111 | "The container needs `google-adk[otel-gcp]` or it boot-crashes on the unconditional Cloud Logging import (`telemetry/google_cloud.py:272`)." | The page names the wrong package for the boot crash. Line 272 imports `opentelemetry.exporter.cloud_logging`, which comes from the `opentelemetry-exporter-gcp-logging` package. The `[otel-gcp]` extra installs only three instrumentation libraries (google-genai, grpc, httpx), checked with `importlib.metadata.requires("google-adk")`. | "The container needs `opentelemetry-exporter-gcp-logging` and `opentelemetry-exporter-otlp-proto-http`, or it crashes on boot at the Cloud Logging import (`telemetry/google_cloud.py:272`). `demo_agent/requirements.txt` pins both." | still real |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F170 | 51–52, 54–60 and 86 | The `describe`, `delete` and curl commands | Several flags share one line, which is hard to scan. | Put each flag on its own line. | still real |
| F171 | 94 and 105 | "Where .env goes and why the location is repeated"; "Two deploy traps" | House style writes deep-dive headings as questions. | Rename both to questions. | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F172 | 96–97 | "`adk deploy cloud_run` copies the whole agent folder, including `demo_agent/.env`" | The page assumes a `demo_agent/.env` exists. It is gitignored and Setup never creates it, so a reader following the tutorial ships no such file. | "…including a `demo_agent/.env` if you created one." Setup needs a matching fix (see the 00-setup finding). | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F173 | 46–79 | No Expected output in Steps 2 and 3 | The reader cannot tell whether their run worked. | Add a trimmed response and one log entry from a real run to each step. | still real |

### tutorial/part-5/5.5-your-own-server.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F174 | 134–135 | "Curl the service, read `gen_ai.*` back as in Step 2 (the resource `job` is now the Cloud Run service, content `<elided>`)" | Step 4 expects log entries that never arrive. In the rerun on jwd-dev-4, `/chat` answered but no `gen_ai.*` entries reached Cloud Logging; the service logged `Failed to export logs batch code: 400`. The image installs `google-adk[otel-gcp]>=2.8.0`, which now gets 2.11.0, and 2.11.0's log export needs a `gcp.project_id` this server never sets. Steps 1–3 work because the local `.venv` has 2.8.0. Even on 2.8.0, this server does not detect Cloud Run (`telemetry/setup.py:117-122`), so `job` stays `weather-agent`. | Pin `google-adk[otel-gcp]==2.8.0` in the image (see the requirements.txt finding below). Change the parenthetical to "(the `job` is still `weather-agent`; this path does not detect Cloud Run)". | still real (the `>=2.8.0` cause is fixed on main; the `job` claim remains) |
| F175 | 64–66 | "They land on a `generic_task` resource whose `job` is your `OTEL_SERVICE_NAME` (`weather-agent`)" | The resource type is wrong. OpenTelemetry's GCP resource detector uses `generic_task` only when both `service.name` and `service.instance.id` are set (`opentelemetry/resourcedetector/gcp_resource_detector/_mapping.py:164-173`). Otherwise it uses `generic_node`, which has no `job` label. `.env.example` sets no `OTEL_RESOURCE_ATTRIBUTES`. The author's gitignored `.env` sets `service.instance.id=laptop-1`, which is why the page's capture worked. The rerun on jwd-dev-4 confirmed it. | "Set `OTEL_RESOURCE_ATTRIBUTES=service.instance.id=laptop-1` so the entries land on `generic_task` with `job` = `weather-agent`." | still real |
| F176 | 104 | "Every `gen_ai.*` entry now reads `<elided>` in the content field" | Step 3 also turns on the experimental event format. In that format, with this server (where ADK emits the events itself), `NO_CONTENT` leaves the content fields out entirely (`_experimental_semconv.py:611-625`). `<elided>` appears only in the default format. The rerun on jwd-dev-4 confirmed it. | "Each entry is now one `gen_ai.client.inference.operation.details` event with no `gen_ai.input.messages` or `gen_ai.output.messages` field." | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F177 | 71–73 | "it carries `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`, so the Step 1 entries show the prompt and reply text. Comment out that `true` line if it is there" | The Step 1 content setting cannot be reproduced. `.env.example` has no `=true` line, so a new reader's Step 1 shows no content, and Step 3's before and after cannot be reproduced. The rerun on jwd-dev-4 showed no content in the working tree too, because the author's `.env` holds `NO_CONTENT` and the experimental format. | "Before Step 1, add `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` to the root `.env`. Step 3 changes it to `NO_CONTENT`." | still real |
| F178 | 113–129 | Step 4's `gcloud run deploy`, with no "not run" label | how-to-choose lists this deploy as not verified, but the page does not say so. | Capture a real deploy and its output. Or add "Not yet deployed; see how-to-choose." | still real |
| F179 | 119–128 | `cp deploy/Dockerfile.otel_server ./Dockerfile … gcloud run deploy … rm -f ./Dockerfile` | `rm` runs only if the deploy succeeds, so a failed deploy leaves `./Dockerfile` in the repo. | Move the commands into a `deploy/` script that removes the file on exit, as the other deploy scripts do. | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F180 | 67 | No mention of traces | This server sets up export for logs only, not traces. With no trace export configured, ADK's spans record nothing, so the log entries carry no `trace` or `spanId`. The rerun on jwd-dev-4 confirmed it, and 5.8's "correlated automatically" does not hold here. | Add "This exports log events only. Spans need `enable_cloud_tracing=True`." | still real |
| F181 | 53, 100 and 145 | `"What is the weather in London?"` | The prompt is spelled three different ways across Part 5. The rest of the part uses a different phrasing for the same question. | Change all three to "What's the weather in London?" | still real |
| F182 | 69 and 79–83 | "**Step 3 — The content knob, set through `.env`.**" | Step labels are verb phrases. The `.env` snippet also sits in a `bash` fence with a `#` line, though it is not shell. | "**Step 3 — Set the content setting in `.env`.**" and put the snippet in a plain fence. | still real |

### tutorial/part-5/5.6-content-knobs.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F183 | 27–29 | "A truthy value like `=true` on the event knob is read as `EVENT_ONLY` for back-compat (`telemetry/context.py:94-101`), which is why 5.2 Step 2's `=true` worked." | The page says `=true` always works as `EVENT_ONLY`. With `--otel_to_cloud` and a Gemini model, the `opentelemetry-instrumentation-google-genai` library emits the events and reads `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` itself (`google_genai/flags.py`), not through ADK's mapping. In the default format only `true` turns content on. In the experimental format only `EVENT_ONLY`, `SPAN_ONLY` and `SPAN_AND_EVENT` work; `true` logs a warning and falls back to `NO_CONTENT` (`opentelemetry/util/genai/utils.py:45-65`). ADK's mapping of `true` to `EVENT_ONLY` applies only when ADK emits the events itself, as on 5.5's server. | "Which value works depends on who emits the events. With the CLI flag, the default format takes `true`, and the experimental format takes `EVENT_ONLY`, `SPAN_ONLY`, or `SPAN_AND_EVENT`. On your own server (5.5), ADK reads it and also accepts `true` (`context.py:94-101`)." | still real |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F184 | 21 | "Read by" (column header) | The column holds source paths, so the header does not describe it. | Rename to "ADK source". | still real |
| F185 | 24 | "**`true`**" | House style does not use bold for emphasis. | Remove the bold. | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F186 | 34 | "including one in `demo_agent/.env`" | The page assumes a `demo_agent/.env`, which is gitignored and never created by Setup. It also omits a limit: per-request `RunConfig.telemetry` does not reach the `generate_content` span when the `opentelemetry-instrumentation-google-genai` library emits it (see "Limitations" in the `TelemetryConfig` docs in `context.py`). | "including one in `demo_agent/.env` if you created it", and add the `RunConfig.telemetry` limit as one sentence after line 42. | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F187 | 44–47 | "**The one place a default is chosen for you.**" | This describes `adk deploy agent_engine`, which belongs to Part 6, so the reader sees an unexplained command. | Replace the passage with one line pointing to 6.1. | still real |

### tutorial/part-5/5.7-other-backends.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F188 | 35–36 | "(… grep for `grpc` in the telemetry package returns nothing)" | It narrates the author's check instead of stating the fact. | "(`telemetry/setup.py` imports only the HTTP exporters)" | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F189 | 13 | "OTLP" | No expansion appears anywhere in Part 5, so the reader cannot tell what the acronym stands for. | Write "OTLP (the OpenTelemetry protocol)" at first use. | still real |

### tutorial/part-5/5.8-relates-to-parts-1-4.md

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F190 | 22–34 | Bold used for emphasis throughout the table | House style does not use bold for emphasis. | Remove it. | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F191 | 20–25 | The table's `#` column numbering "four places" 1 to 4 | The "four places" do not match the four streams. Place 1 is stream 2, place 2 is stream 1, and places 3 and 4 are both stream 4. | Drop the `#` column and label each row by its stream. | still real |
| F192 | 51 | "That leaves one place, not four." | The advice keeps spans and `gen_ai.*` events, which are two places. | "That leaves two, spans and events, joined by trace id." | still real |
| F193 | 34; 5.2 line 116 | "Part 4's `X-Cloud-Trace-Context` trace ↔ OTel span trace \| **Different trace ids**" | 5.2 says the trace join is free and 5.8 says the ids differ. 5.2's "Part 4 built this join by hand… here it is free" will be read to mean the same ids. | In 5.2, change the sentence to "OTel does this join with its own trace ids, which are not Part 4's." | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F194 | 34 | "`cli/fast_api.py:531-547` handles only the Agent Engine header" | This omits the `traceparent` header. `telemetry/_agent_engine.py:63-69` also reads a standard W3C `traceparent` header, but only stores it as extra context, not as the parent of ADK's spans. The page's conclusion (ADK never reads `X-Cloud-Trace-Context`) still stands. | Add "(a standard `traceparent` header is recorded, but not used as the parent span)". | still real |

### tutorial/part-6/index.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F195 | 27–28 | "There is no `--otel_to_cloud` flag reaching a server process here. Telemetry is governed by one env var on the deployment" | The page says no flag reaches the server, but one does. In ADK 2.8.0, `adk deploy agent_engine` deploys a container that starts `adk api_server`. Both Part 6 methods (the flag in 6.2, the `.env` line in 6.3) make the CLI add `--otel_to_cloud` to that start command (`cli_deploy.py:1273-1292`, `:1392`). The 6.3 rerun printed "`--otel_to_cloud` is set to True by GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY". | "`adk deploy agent_engine` builds a container that runs `adk api_server`. Passing `--otel_to_cloud`, or setting `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` in `.env`, puts `--otel_to_cloud` on that server's start command and sets the env var on the deployment." | still real |
| F196 | 16 | "On a native deploy you do not run uvicorn or write JSON lines" | The deployed container does run uvicorn. The generated container runs `adk api_server`, which serves through uvicorn. The page's own "access lines on `reasoning_engine_stdout`" are uvicorn's. | "On a native deploy you do not write the server; the CLI generates one that runs `adk api_server`." | still real |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F197 | 16–29 | Three body paragraphs, about 315 words | House style keeps a landing page to one paragraph of about 200 words. | Cut to one paragraph of about 200 words. | still real |
| F198 | 35–38 | The link text in the "In this part" table | The link text is not each page's full H1. | Use each page's full H1 as the link text. | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F199 | 22–25 | "Your Part 4 structured plugin works here unchanged… Drop the trace-header parsing, because the platform handles request correlation." | The Part 4 plugin claim was never run in Part 6. Nothing in Part 6 runs the plugin, and How to choose does not list it as unverified. | Label the claim "Not run in this tutorial" and add it to the Not verified table in How to choose. | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F200 | 7–25 | "Vertex AI Agent Engine", "Agent Engine", and "Agent Runtime" all appear; "native deploy" is defined only in 1.6. | The same product has three names. A reader cannot tell whether these are one product or three, and has to go back to 1.6 for "native deploy". | Write "Agent Runtime (deployed with `adk deploy agent_engine`, not your own container)" once, then "Agent Runtime" throughout. | still real |

### tutorial/part-6/6.1-one-switch.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F201 | 13–14 | "The `AdkApp` wrapper reads it at startup." | `AdkApp` is not what reads the variable on this deploy. `AdkApp` does read it (`vertexai/agent_engines/templates/adk.py:1780-1792`: `true` or `1` on, `false` or `0` off). But 2.8.0 `adk deploy agent_engine` deploys a container running `adk api_server`, not an `AdkApp` (`cli_deploy.py:1424`). There the CLI reads the variable at deploy time and adds `--otel_to_cloud` to the start command. In this tutorial `AdkApp` runs only in the bring-your-own-container (BYOC) image (`agent_runtime_byoc/main.py:56`). | "On a deploy with `adk deploy agent_engine`, the CLI reads the variable when you deploy and adds `--otel_to_cloud` to the container's `adk api_server`. A BYOC container built on `AdkApp` reads it at startup: `true` or `1` turns telemetry on, `false` or `0` turns it off." | still real |
| F202 | 37–38 | "The BYOC script here passes only project, location, and log level" | The BYOC script passes three other variables. `agent_runtime_byoc/deploy_byoc.py:53-60` passes `LOG_LEVEL`, `GOOGLE_GENAI_USE_VERTEXAI`, and `MODEL_LOCATION`. The platform injects project and location. | Name those three variables in the sentence. | still real |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F203 | 19, 23, 24, 26 | "they are not equivalent", "you", "and", "the CLI sets no content knobs" | House style does not use bold for emphasis inside running text. | Remove the bold. | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F204 | 23 | "`ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` (the span knob, set safe for you)" | The setting only covers span content. It turns off message content on spans only. The page never names the setting for content in log events, `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`, which first appears in 6.3. | "The flag turns off message content on spans only. Content in the `gen_ai.*` log events is controlled by `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`, which stays at its default unless you set it. See [5.6](../part-5/5.6-content-knobs.md)." | still real |
| F205 | 24 | "`cli/cli_deploy.py:1283-1291`" | The source citation is off by one and incomplete. The block ends at line 1292, and its only effect is setting `otel_to_cloud`. The value must be lowercase `true` or `1`. | "`google/adk/cli/cli_deploy.py:1283-1292` (google-adk 2.8.0); the value must be `true` or `1`." | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F206 | Whole page | No "Why you are here" note, no command, no handoff | This is a concept page with no step, command, or handoff. The two other ways to set the variable (the SDK's `update` call and the Console toggle) were never run, so they and the BYOC note are side material. | Add the "Why you are here" note and the handoff "6.2 deploys with the flag.", and move the side material under `## Deep dives`. | still real |

### tutorial/part-6/6.2-deploy-flag.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F207 | 131 | No teardown step | The engine is deployed and never torn down. The page deploys an Agent Runtime engine, and 6.3 deploys a second one with the same `display_name`. How to choose says "Both engines deleted after the runs", but the reader is never told how. The rerun on jwd-dev-5 showed both engines still listed until the reviewer deleted them. | "**Step N — Tear down.**" with the delete command for `$ENGINE_ID` (and `$ENGINE_ID_ENV` in 6.3). Or link to 1.6's teardown. | still real |
| F208 | 13–14 and 125–126 | "The flag makes the CLI write the telemetry vars; the `.env` carries only the base config." | The flag does more than write telemetry variables, and the citation is off. The flag also adds `--otel_to_cloud` to the container's start command (`cli_deploy.py:1392`). The cited `cli_deploy.py:1230-1234` only reads `.env` into the deployment's env vars; the agent folder is copied into the image elsewhere (`:1419-1424`). | "The flag writes the telemetry vars into the deployment's env and adds `--otel_to_cloud` to the server command. `cli_deploy.py:1226-1234` reads `.env` into the env vars, and the agent folder, `.env` included, is copied into the image." | still real |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F209 | 94 and 105 | "stderr", "no `gen_ai.*`" | House style does not use bold for emphasis inside running text. | Remove the bold. | still real |
| F210 | 123 | "### Why the copy and restore" | House style writes deep-dive headings as questions. | "### Why copy a `.env` in before deploying and restore it after?" | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F211 | 102–110 | "Where the OTel telemetry lands on a native deploy is an open question", under "What Agent Runtime does NOT do, that Cloud Run did." | The callout blames a platform difference that does not exist. The heading implies Agent Runtime works differently from Cloud Run. It runs the same `adk api_server --otel_to_cloud` command that works on Cloud Run in 5.4, so that can't explain why nothing arrived. The rerun on jwd-dev-5 got the same result as the page: no `gen_ai.*` logs, no traces, no export errors. | "**What it means.** Agent Runtime started the same `adk api_server --otel_to_cloud` as Cloud Run, but no `gen_ai.*` events reached Cloud Logging and no spans reached Cloud Trace in 40 minutes of queries. See [Not verified](../how-to-choose.md#not-verified)." Worth checking: whether the image installed the export packages in `demo_agent/requirements.txt`, and whether the engine's service account can write to Cloud Trace and Cloud Logging. | still real |
| F212 | 112–118 | "Restore the base `.env` so the deploy's `LOG_LEVEL` does not leak into a local `adk web` run." with `cp deploy/env/default.env demo_agent/.env` | The restore step leaves `LOG_LEVEL` in place. `default.env` itself sets `LOG_LEVEL=info`, and `demo_agent/agent.py:29-33` applies that over `--log_level`. This breaks 1.3's WARNING step if the reader repeats it (seen in the rerun on jwd-dev-1). The copy also overwrites any `demo_agent/.env` the reader had. | Drop `LOG_LEVEL` from `default.env`. Or back up the reader's file first with `cp demo_agent/.env /tmp/demo_agent.env.bak`, then restore it after with `cp /tmp/demo_agent.env.bak demo_agent/.env`. | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F213 | 94–100 | Expected output for the query step shows one set of three INFO lines | The expected output is shorter than a real run. The rerun on jwd-dev-5 showed each set twice (two model calls), Python `FutureWarning` and `UserWarning` lines on stderr, and the stdout access line. Each deploy also printed "Ignoring GOOGLE_CLOUD_LOCATION in .env as --region was explicitly passed", which the page never mentions; the env list still reads `global`. | Label the block "(trimmed)" and add one sentence explaining the `GOOGLE_CLOUD_LOCATION` notice. | still real |
| F214 | 33 | "**Read the deployment's env list.**" (no `**Step N — …**` labels) | House style uses numbered step labels, a "Why you are here" note, and a handoff sentence. The page has none, and does not warn that the deploy takes several minutes. | Add the step labels, the note, the handoff, and a line saying the deploy takes several minutes. | still real |
| F215 | 33–34 | "`gcloud ai` has no reasoning-engine subcommand in every install" | The page contradicts How to choose on `gcloud ai`. How to choose says the subcommand "does not exist in this install". The two pages disagree, and "in every install" is vague. | "`gcloud ai` has no command that reads an engine's env, so use the `vertexai` SDK." | still real |
| F216 | 39 and 72 | `$GOOGLE_CLOUD_PROJECT` (lines 39 and 72) and `$PROJECT_ID` (lines 19, 23 and 89) | The page uses two names for the project. A reader will wonder whether they are different values. | Use `$PROJECT_ID` throughout. | still real |

### tutorial/part-6/6.3-deploy-env.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F217 | 105 | No teardown step | The second engine is never torn down. The page deploys a second engine and never deletes it. The same gap exists in 6.2. | Add a "**Step N — Tear down.**" with the delete command for `$ENGINE_ID_ENV`, shared with 6.2's teardown. | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F218 | 13–14 | "the deploy drops `--otel_to_cloud`" | The CLI does add the flag. It reads `true` from `.env` and adds `--otel_to_cloud` to the container's start command itself (`cli_deploy.py:1287-1292`, `:1392`). The rerun on jwd-dev-5 printed "`--otel_to_cloud` is set to True by GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY". | "the command omits `--otel_to_cloud`; the CLI reads the `.env` value and adds the flag to the server command itself." | still real |
| F219 | 65–66 | "Had `6.2b.env` omitted the span knob, prompt text would ride on the spans." | The page states as fact something 6.2 could not observe. It asserts this right after 6.2 found no spans at all on Agent Runtime. | "…the span attributes would carry prompt text (default `true`, `google/adk/telemetry/context.py:108-110`), though no spans appeared on Agent Runtime in these runs." | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F220 | 13–14 and 64 | "both content knobs" and "the event knob" | The content settings are named but never defined. The page does not say what these are or link to 5.6. | Name `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` once (it controls prompt and reply text in log events), with a link to 5.6. | still real |
| F221 | 73–94 | 6.2's whole query fence, repeated, with no output | The page repeats 6.2's query and shows no output. The reader sees a long command and no result. | "Run 6.2's query; the output is the same." | still real |

### tutorial/part-6/6.4-platform-changes.md

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F222 | 17 | "The enablement switch \| One env var… Both routes set it to `true`." | Enabling telemetry also adds a server flag. Both methods also add `--otel_to_cloud` to the server's start command (see 6.1). | "Both methods set the variable to `true` and add `--otel_to_cloud` to the server's start command." | still real |
| F223 | 25–28 | "If you scaffold with `agents-cli`, the generated project wires a `setup_telemetry()` … `LOGS_BUCKET_NAME` (exported to GCS and BigQuery). That is the same OTel machinery from Part 5, pre-wired." | This is an unrun claim about a different tool. No page runs this, How to choose does not list it as unverified, and `agents-cli` is a separate tool, not the pinned ADK. | Delete the paragraph. Or replace it with "For other export targets, see [5.7](../part-5/5.7-other-backends.md)." | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F224 | 12–28 | No step, no command | The page has no step and restates 6.2 and 6.3. The content repeats what 6.2 and 6.3 already cover. | Fold it into 6.3 as a short closing table. Or reframe it as a decision table. | still real |
| F225 | 22 | "Do not extend this list past what you can see in your own project's console." | The closing advice is vague. The reader is not told where to look or why. | "Check your own project's Trace Explorer and Logs Explorer; this tutorial did not establish where Agent Runtime sends telemetry." | still real |

### tutorial/how-to-choose.md

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F226 | 63 and 67 | "Every console block in the tutorial is from one of these runs." | 4.3 has no run row and sits under Not verified. The "1.1–1.3, 3.1, 3.3, 4.1, Part 2" row has no date. | Fill in the date, add 4.3 to Not verified explicitly, and reword to "Every console block except those under Not verified…". | still real |

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F227 | 32–33 | "Emit **one JSON object per line** with an explicit **`severity`**, to **stdout**." | House style does not use bold for body phrases. | "Write one JSON object per line to stdout, with an explicit `severity`." | still real |

**Misleading**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F228 | 36 | "Keep GenAI content capture at **`NO_CONTENT`** unless you have a reviewed reason." | `NO_CONTENT` leaves prompt text on trace spans. In ADK 2.8.0 it governs only the `gen_ai.*` log events. Span attributes are governed by `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS`, which defaults to true (`google/adk/telemetry/context.py:108`). | "Turn content capture off in both places: `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT` for log events and `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` for span attributes (5.6)." | still real |
| F229 | 82 | "Whether `=true` also puts the prompt and reply on the `call_llm` span… and whether `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` empties them" | The pinned ADK source already answers both Not verified questions (`tracing.py:629`). | State the answer from the source, and keep only "not yet observed in Trace Explorer" as the unverified part. | still real |
| F230 | 20 | "Emitting metrics for production \| Custom `BasePlugin` (4.1)" | The 4.1 plugin emits log events, not metrics. | Change the first cell to "Emitting structured events you can query and alert on". | still real |
| F231 | 25 | "`adk deploy agent_engine` (1.6) + `--otel_to_cloud`" | The row implies telemetry arrives. The page's own Not verified table records that none did. | Add "Telemetry did not surface in our runs; see Not verified." | still real |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F232 | 87 | "**verified negative**" (in the Not verified table) | Something checked and found absent is a verified result, so the table title contradicts the row. | Retitle the table "Not verified or inconclusive". Or move the row to the run table. | still real |
| F233 | 89–92 | "**Re-run checklist for Part 5:** … `export OTEL_RESOURCE_ATTRIBUTES=…`" | These are steps on a reference page, and the `…` leaves the export incomplete. | Replace the checklist with "To rerun Part 5, follow 5.2's exports." | still real |
| F234 | 72 and 74–76 | The "What it showed" cells for 5.2, 5.4, 5.5, and 6.2/6.3 | They are walls of text. They pack run records, trace-id prefixes, and terms such as `prometheus_target` and `generic_task` into one cell. | Keep one or two facts per cell and leave the details to the pages that teach them. | still real |
| F235 | 23 and 56 | "severity is Cloud Run's guess (Default)" and "The ADK observability skill and `https://adk.dev/observability/` cover these." | "Cloud Run's guess" is not a term readers know, and a reader cannot open the skill. | "severity is `DEFAULT` (unset)" and "See the [ADK observability docs](https://adk.dev/observability/)." | still real |
| F236 | 27 | No decision row for silencing health checks | The decision table skips the Part 2 topic. | Add "Silencing health-check access lines \| A filter on `uvicorn.access` (Part 2)". | still real |

### agent_runtime_byoc/

**Style**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F237 | requirements.txt 1; deploy_byoc.py 1 and 44; main.py 1 and 12; Dockerfile 1 | "tutorial 1.7", "Tutorial 1.7: naive Part 1 logging" (docstrings and deploy description) | The page is now 1.6, so these references are stale. | Change "1.7" to "1.6". | done (after the 1.6/1.7 split the BYOC page is 1.7 again, so the files are right; `deploy_byoc.sh` updated to 1.7) |

**Unclear**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F238 | deploy_byoc.sh 83 | the logs "land under reasoning_engine_stdout" | `basicConfig` writes to stderr, and 1.6 reads stderr for the native deploy. | Name the stream the BYOC run actually used, and state it in 1.6's BYOC table too. | done |

### deploy/deploy_agent_engine.sh

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F239 | 41 | `printf "%s\n" "$_ORIG_ENV" > ./demo_agent/.env` (in the trap) | It recreates `demo_agent/.env` even if none existed. ADK then finds that file first and never loads the root `.env`, so a later `adk web` loses its model config. | Record `_HAD_ENV` before the write, then use `trap '[ -n "$_HAD_ENV" ] && printf … \|\| rm -f ./demo_agent/.env' EXIT`. | done |

### deploy/deploy_job.sh and deploy/deploy_api.sh

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F240 | deploy_job.sh 53; deploy_api.sh 47 and 63 | `deploy_job.sh:53` "its records are written to stderr, which Cloud Run records as ERROR severity" and `deploy_api.sh:63` "…ERROR severity. That is the "before" the rest of the tutorial fixes." | 1.4 and 1.5 both find Default severity, so the scripts contradict the pages. `deploy_api.sh:47` also suggests a `severity>=ERROR` query that returns nothing. | Change both to "…which Cloud Run records with Default severity (see 1.4)." Replace the `severity>=ERROR` query in `deploy_api.sh:47`. | done |

### requirements.txt

**Wrong**

| ID | Lines | Text on the page | Problem | Fix | Status |
|---|---|---|---|---|---|
| F241 | 1 and 5 | "# Verified against google-adk 2.8.0", with the pin `google-adk[otel-gcp]>=2.8.0` | The header claims 2.8.0 but the pin allows 2.11.0. A fresh install or image build gets 2.11.0 (current on PyPI), which breaks 5.5 Step 4's log export (see 5.5). | Change the pin to `google-adk[otel-gcp]==2.8.0`. Or test the newer version and document it. | fixed on main (all three requirements files pin `==2.8.0`) |

---

## Demo runs

"Matches" means the output had the same shape the page shows (the same logger names, fields, and events), with timestamps, ids, and the model's wording differing as expected from a live model. "One question" means one prompt sent to the agent, such as "What's the weather in London?".

| Page | Project | What was run | Result |
|---|---|---|---|
| Setup | jwd-dev-1 | `pip check` and the installed versions | Matches. The existing virtual environment was checked, not recreated. |
| 1.1 | jwd-dev-1 | `examples/01_log_levels.py` at `info`, `debug` and `warning` | Differs. Every level also prints a Python `UserWarning` about an experimental ADK feature, so WARNING is not silent. INFO adds `Closing runner…` lines; DEBUG adds `Config:` and `Raw response:` sections. No bearer token appeared, as the page claims. |
| 1.2 | jwd-dev-1 | `adk web --log_level INFO ./`, then one question through `/run` | Matches. |
| 1.3 | jwd-dev-1 | `adk api_server` at `INFO`, the page's curl calls | Matches, including the 409 on a second session create. |
| 1.3 | jwd-dev-1 | `adk api_server --log_level WARNING ./` | **Differs:** every INFO line still printed, because the gitignored `demo_agent/.env` holds `LOG_LEVEL=info`. With `export LOG_LEVEL=warning`, the output matched. |
| 1.4 | jwd-dev-1 | `deploy/deploy_job.sh`, an INFO and a WARNING run, `gcloud logging read` | Matches: blank severity. INFO also logged two `httpx` request lines. No batching was seen. |
| 1.5 | jwd-dev-1 | `deploy/deploy_api.sh` twice, curl, `gcloud logging read` | Matches, plus an `httpx` logger the page's "four sources" leaves out. |
| 1.6 | jwd-dev-1 | `deploy/deploy_agent_engine.sh` and `stream_query` | Matches. |
| 1.6 | jwd-dev-1 | `agent_runtime_byoc/deploy_byoc.sh` and the curl query | First attempt **failed** with "failed to start and cannot serve traffic". An unchanged rerun succeeded. |
| 1.6 | jwd-dev-1 | `gcloud logging read` for each engine | **No entries** in about 10 minutes, though both engines answered. The page's two log tables could not be checked. |
| Part 2 | jwd-dev-2 | `examples/02_tame_uvicorn.py`, three `/healthz` requests and one `/` | Matches. |
| 3.1 | jwd-dev-2 | `examples/03_logging_plugin.py` | Same structure, but 64 plugin lines for one question, not 29. |
| 3.2 | jwd-dev-2 | `deploy/deploy_plugin_job.sh`, a WARNING run, both log reads | Severity matches. WARNING also hid the tool's own line. The `logging_plugin` read **differs**: it returns the 10 newest lines, not "the full narration for both runs", and also matches a framework line. |
| 3.3 | jwd-dev-2 | `examples/04_debug_plugin.py`, `cat adk_debug.yaml` | **Differs:** the file has a header and per-entry fields the page omits, and each run appends another document. |
| 3.4 | jwd-dev-2 | `deploy/deploy_plugin_job.sh` with `MOUNT=1`, `gcloud storage cat`, teardown | Two plugin warnings in Cloud Logging, not one. The script created a bucket that the page's teardown leaves behind. |
| 4.1 | jwd-dev-3 | `examples/05_structured_plugin.py` | **Differs:** 6 lines per question, not 3, each with `logger` and `event` fields. |
| 4.2 | jwd-dev-3 | `examples/06_custom_server.py`, curl with a trace header | **Differs:** the access line has no trace; every line has `sourceLocation`; no OpenTelemetry output. |
| 4.3 | jwd-dev-3 | `deploy/deploy_cloudrun.sh`, both log reads, teardown | The `jsonPayload.message:*` read **differs**: 8 rows per question, newest first, plus two startup rows. The `tool_end` read matches. |
| 4.4 | jwd-dev-3 | `gcloud logging read` with `jsonPayload.logger="agent.telemetry"` (an extra check of the page's claim) | **No entries.** |
| 5.1 | jwd-dev-4 | `adk web ./`, one question, the trace endpoint | Matches. |
| 5.2 | jwd-dev-4 | Steps 1 to 5 with `--otel_to_cloud` | Matches, except the span check: spans were empty in the working tree (because of `demo_agent/.env`) and full in a clean copy. Metric export failed with HTTP 400 without `OTEL_RESOURCE_ATTRIBUTES`, as the page says. |
| 5.3 | jwd-dev-4 | `adk api_server --otel_to_cloud`, curl | Matches what the page describes; the page shows no output. |
| 5.4 | jwd-dev-4 | `adk deploy cloud_run … --otel_to_cloud`, the log query | **Differs:** eight events in the default format and no `operation.details` events. |
| 5.5 | jwd-dev-4 | `examples/08_otel_server.py`, Steps 1 to 3 | **Depends on the author's `.env`.** Without `service.instance.id` the resource is `generic_node` with no `job`. With the experimental format, content is absent, not `<elided>`. |
| 5.5 | jwd-dev-4 | Step 4, the Cloud Run deploy | **Fails:** no `gen_ai.*` entries; `Failed to export logs batch code: 400`. |
| 6.2 | jwd-dev-5 | `adk deploy agent_engine --otel_to_cloud`, the env read-back, a query, the log read | Matches: five env lines, INFO lines on stderr, no `gen_ai.*` logs and no traces after about 10 minutes. |
| 6.3 | jwd-dev-5 | The same, without the flag | Matches. The CLI printed "`--otel_to_cloud` is set to True by GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY". |

**Where the reruns departed from the pages:**
- Every shell exported `PROJECT_ID`, `GOOGLE_CLOUD_PROJECT` and the other variables for its dev project instead of sourcing `env.sh`, which names `jwd-gcp-demos`. The shell values took precedence over the root `.env` in every run.
- Browser steps were replaced by the equivalent API calls: `/run` for the chat box, the trace endpoint for the Trace tab, `gcloud logging read` for Logs Explorer, and the Cloud Trace API for Trace Explorer.
- Some Part 5 steps were also run in a clean copy of `demo_agent/` whose `.env` held only what `.env.example` gives a new reader.
- Parts were run one at a time, because the deploy scripts share `./Dockerfile` and the local servers share ports 8000 and 8080.

### Skipped demos

| Demo | Reason |
|---|---|
| Setup: creating the virtual environment and installing packages | The existing environment was checked instead. |
| Browser-only views (the `adk web` chat box and Trace tab, Logs Explorer, Trace Explorer) | Replaced by the API calls listed above. |
| 3.5, 4.4, 5.0, 5.6 to 5.8, 6.1, 6.4 | These pages have no commands to run. |

No demo was skipped for cost.

---

## Inconsistencies between pages

| # | Inconsistency | Pages | Status |
|---|---|---|---|
| 1 | `demo_agent/.env` has no owner. Setup never creates it, later pages write it, read it, and ship it in images, so what a page shows depends on which page ran last. | Setup, 1.3, 1.6, 5.1 to 5.6, 6.2, 6.3 | still real |
| 2 | The two content settings are explained four ways. 5.4 says the span setting hides log content; 5.6 says the two are independent; how-to-choose turns off only the log setting; 5.6's rule for `true` holds only when ADK writes the events itself. | 5.2, 5.4, 5.6, 6.1, 6.3, how-to-choose | still real |
| 3 | Pages show `operation.details` events without saying they need `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`. 5.4 doesn't set it. | 5.2, 5.3, 5.4, 5.5 | still real |
| 4 | "All four streams" appears before any page sets up stream 4 (OpenTelemetry). 1.5's "four sources" and 5.8's "four places" reuse the number for other things. | Part 1 index, 1.5, Part 4, 4.2, 5.8 | still real |
| 5 | Three names for one product: Agent Runtime, Agent Engine, and Vertex AI Agent Engine. "Native" and "BYOC" are defined only in 1.6. | README, TUTORIAL, 1.6, Part 6, how-to-choose | still real |
| 6 | How telemetry is turned on for Agent Runtime: Part 6 describes an `AdkApp` reading an environment variable; the CLI actually starts `adk api_server --otel_to_cloud`. | 1.6, Part 6, how-to-choose | still real |
| 7 | Stderr severity: the pages say blank (Default), the deploy scripts' closing messages say ERROR. | 1.4, 1.5, `deploy/deploy_job.sh`, `deploy/deploy_api.sh` | still real |
| 8 | One log call shown at three line numbers: `agent.py:40`, `:53` and `:54`. It is at `:54` now. | 1.3, 1.6, 6.2 | still real |
| 9 | The standard question drifts: Paris, New York, "weather in Tokyo?" and "What is the weather…" instead of the Tokyo or London question. | 3.3, 3.4, 4.1, 4.2, 5.5 | still real |
| 10 | Expected output shows one model call where a tool question makes two, without saying it is trimmed. | 1.4, 4.1, 4.2, 4.3, 6.2 | still real |
| 11 | "Every block is from a real run", while 4.3's table doesn't match a real run and 5.3 and 5.5 Step 4 show no captured output. None is marked unverified. | TUTORIAL, how-to-choose, 4.3, 5.3, 5.5 | still real |
| 12 | Only Part 5 numbers a page N.0. | 5.0 | still real |
| 13 | The tutorial's `CLAUDE.md` gives a page order that stops at Part 3. | `CLAUDE.md` | still real |
| 14 | BYOC files still call the page "tutorial 1.7". | `agent_runtime_byoc/`, 1.6 | still real |
| 15 | Pages over the 750-word limit: 1.4 (812), 1.5 (752), 1.6 (about 1,750), 3.1 (865), 5.1 (852), 5.2 (about 2,020). | 1.4, 1.5, 1.6, 3.1, 5.1, 5.2 | still real |
| 16 | Most pages lack the "Why you are here" note, `**Step N — …**` labels, or a closing sentence that introduces the next page; deep-dive headings are statements, not questions. | Most pages in Parts 1 and 3 to 6 | still real |

---

## Leftovers

**Cloud resources this review created:** all Cloud Run services and jobs, Agent Runtime engines, and storage buckets are deleted.

| Project | Created | Deleted |
|---|---|---|
| jwd-dev-1 | Cloud Run job `adk-logging-job`, services `adk-logging-api` and `adk-logging-api-warn`, two Agent Runtime engines | Yes |
| jwd-dev-1 | Artifact Registry repositories `adk-logging` and `cloud-run-source-deploy` | **No.** The deletion command was blocked by a permission check. Delete with `gcloud artifacts repositories delete <repo> --location=us-central1 --project=jwd-dev-1 --quiet`. |
| jwd-dev-1 | Two project-level `roles/artifactregistry.reader` grants to Vertex service agents, added by `deploy_byoc.sh` | No. They let Agent Runtime pull the BYOC image. |
| jwd-dev-2 | Cloud Run jobs `adk-plugin-job` and `adk-debug-plugin-job`, bucket `gs://jwd-dev-2-adk-debug` | Yes |
| jwd-dev-3 | Cloud Run service `adk-logging-demo` | Yes |
| jwd-dev-4 | Cloud Run services `adk-logging-otel` and `adk-otel-server`; Artifact Registry repository `cloud-run-source-deploy` and bucket `run-sources-jwd-dev-4-us-central1` | Services yes; repository and bucket **no** |
| jwd-dev-5 | Two Agent Runtime engines | Yes |

**Left in place on purpose:** container images and source archives that the deploys pushed into existing `cloud-run-source-deploy` repositories and `run-sources-…` buckets in jwd-dev-2 and jwd-dev-3. After the jwd-dev-1 deletion was blocked, later reruns were told to list these rather than delete them.

**jwd-gcp-demos:** nothing was written.

**Gitignored files touched:** `adk_debug.yaml` (appended by 3.3, restored byte for byte) and `demo_agent/.env` (overwritten by 6.2's restore step, restored byte for byte). `demo_agent/.adk/session.db` gained sessions.

**A process this review should not have stopped:** the Part 2 rerun freed port 8081 by stopping pid 74107, a static "Supplementary Materials" web server it did not start. Restart it if you need it.

**Untracked files reported by `git status --porcelain`:**

| When | Untracked files |
|---|---|
| Before the demos | none |
| After the demos | `docs/adk-metrics-review-2026-10-02.md`, `docs/adk-metrics-style-review.md`, `docs/adk-tracing-review-2026-10-02.md` |

All three came from separate sessions reviewing other tutorials at the same time, not from this review.

---

## Appendix: the standards this review applied

The standards come from four sources, listed here in the order they win when two disagree:

1. **The tutorial-review skill:** `.claude/skills/tutorial-review/SKILL.md`.
2. **This tutorial's conventions:** `ai/adk/logging/CLAUDE.md`.
3. **The house tutorial style:** `.claude/skills/tutorial-style/SKILL.md` and the reference files in that folder.
4. **Jeff's global writing rules** (the Writing section of `~/.claude/CLAUDE.md`), and Jeff's tutorial pedagogy note (`feedback-tutorial-pedagogy.md` in the project memory).

**Where sources disagreed:**

| Topic | Standard applied | Standard overridden |
|---|---|---|
| Em dashes | House tutorial style: em dashes only in step labels. | Global writing rules, which allow one or two per large chunk of text. |
| Expected output | This tutorial's conventions: every console block must be captured from a real run. | The pedagogy note, which treats captured output as a strong preference. |

### Standards this review found broken

| Standard | Source | Pages where it was broken |
|---|---|---|
| Claims match the installed ADK and google-genai. | Review skill | Throughout, most in Parts 4 to 6 |
| Commands produce the output the page shows and claims. | Review skill | 1.1, 1.3, 1.4, 3.1 to 3.4, 4.1 to 4.3, 5.4, 5.5, 6.2 |
| Show only output captured from a real run, and label anything else. | This tutorial's conventions | TUTORIAL, how-to-choose, 4.3, 5.3, 5.5 |
| Avoid shorthand: no compressed labels, metaphors or jargon a newcomer to ADK wouldn't know. | Review skill | README, Part 1, 3.1, 3.4, 4.2, 4.4, Part 5, Part 6 |
| Keep each page's story consistent and its advice sensible. | Review skill | Part 2, 3.4, 3.5, 4.4, 5.8, Part 6, how-to-choose |
| Keep the four-streams model and its numbering consistent. | This tutorial's conventions | Part 1 index, 1.3, 1.5, 4.2, 5.0, 5.8 |
| Follow the subtask template: "Why you are here" note of at most two sentences, steps, teardown, a closing handoff sentence, deep dives. | House style | Most pages |
| Structure each step with a `**Step N — …**` label, a **Command:**, **Expected output**, and an interpreting callout. | House style | 1.1, 1.2, 1.6, 5.2, 6.2 |
| Bash blocks: one flag per line, `export` on its own line, no `#` comments, no inline `VAR=value command`. | House style | README, Setup, 1.3, 1.5, 1.6, 3.2, 3.4, 4.3, 5.3 to 5.5 |
| Don't use bold or inline code for emphasis. | House style | Throughout |
| Phrase deep-dive headings as questions, and put gotchas there. | House style | 1.2, 1.4 to 1.6, 3.1, 3.3, 4.1, 4.2, 5.1, 5.2, 5.4, 6.2 |
| Use each callout type for its purpose; a WARNING is one sentence. | House style | 1.3, 1.4, 1.6, 3.1, 3.2, 4.3 |
| Keep each page between 200 and 750 words. | House style | 1.4, 1.5, 1.6, 3.1, 5.1, 5.2 |
| Show only the code the lesson needs. | House style; pedagogy note | Setup, 1.3, 1.6, 3.1, 4.2, 6.1 |
| Ask the Tokyo question in Parts 1 and 4, the London question in Parts 3, 5 and 6. | This tutorial's conventions | 3.3, 4.1, 4.2, 5.5 |
| Point to 5.6 for content settings and 5.7 for other backends. | This tutorial's conventions | 6.1, 6.3, 6.4 |
| Deploy scripts clean up after themselves. | This tutorial's conventions | 5.5, `deploy/deploy_agent_engine.sh` |
| Use one term for each concept. | House style | README, Part 6, 5.5 |
| Write browser directions as bullets, one action each. | House style | 1.2, 5.1, 5.2 |
| Show a prompt once per page, then refer to it by name. | House style | 5.2, 6.3 |
| Use em dashes only in step labels. | House style | 1.1, 1.4 to 1.6, 5.2 |
| Answer first; don't close with a summary or hedge a confident conclusion. | Global writing rules | Part 2, 3.1, 4.4, 6.4 |
| On the reference page, record what was verified and keep the "Not verified" table current. | House style | how-to-choose |


## Found while fixing

| ID | Where | Problem | Status |
|---|---|---|---|
| N01 | `requirements.txt`, 1.6 | A venv built from `requirements.txt` has no `vertexai`, so 1.6's `deploy_agent_engine.sh` fails with "Deploy failed: No module named 'vertexai'" and the SDK queries in 1.6 and Part 6 cannot run. | done (pinned `google-cloud-aiplatform[agent_engines,adk]==2.1.0`, the version the author's venv had) |
