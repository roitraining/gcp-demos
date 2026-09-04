# Merge tutorial Parts 4, 5, 6 into one part

Folder: `ai/adk/logging/`. Status: **implemented 2026-09-04.** Decisions locked:
(1) single server, (2) drop the Job, (3) drop the `adk deploy cloud_run` traps
entirely, (4) callback section last, (5) titled "Structured logging", (6) stray
file killed, (7) folded in with the existing working-tree changes. Step C (the
real containerized Cloud Run deploy) is left for Jeff to run; 4.2 is verified
locally and captured from a real run.

## Why

Parts 4 and 5 build a structured plugin and a custom server that owns all four
streams. Part 6 then ignores both: it runs `adk deploy cloud_run` (stock
`api_server`, no custom logging) with `--otel_to_cloud` (a Part 7 concept), then
re-demonstrates the blank-severity problem 1.4/1.5 already showed, and introduces
a *second* JSON formatter. The work of Parts 4–5 is never deployed.

The fix: one part with a single arc. Build the plugin, run it locally. Put it in
a custom server, run that locally. Ship that exact server to Cloud Run and read
the structured entries back.

## Target shape

**Part 4 · Structured logging, laptop to Cloud Run** (file stays `04-production.md`)

| § | Content | Source |
|---|---|---|
| intro | Why: Part 3 prints; you need records you can query, alert on, correlate. | Part 4 intro |
| 4.1 The plugin | `StructuredTelemetryPlugin`, run `05_structured_plugin.py` locally, expected JSON, reserved-field trap. | Part 4 body |
| 4.2 The custom server | `App` + `Runner` + `lifespan`, one `dictConfig`, `TruncateFilter`, **plus** the `ContextVar` trace middleware and the Cloud Logging JSON fields (`severity`, `logging.googleapis.com/trace`). Run locally with the fake `X-Cloud-Trace-Context` header; expected output shows every line (app, plugin, `google_adk`) carrying the trace. | Part 5 body + Part 6 body (facts one & two, both Mermaid diagrams) |
| 4.3 Deploy to Cloud Run | `./deploy/deploy_cloudrun.sh` (now `gcloud run deploy --source`), curl `/chat`, `gcloud logging read` showing `severity=INFO` and `jsonPayload.*` columns, a trace-grouped query. Traps: model region env var. | Part 6 §6.1, rewritten around the custom server |
| 4.4 Callback or plugin? | Unchanged text. | Part 4 §4.1 |

Dropped from the current parts:

- Part 4's Cloud Run **Job** deploy of `05_structured_plugin.py` (`deploy_plugin_job.sh`). 4.3 makes the same `jsonPayload` point on the real service.
- Part 6 §6.1's `adk deploy cloud_run` flow and its blank-severity re-demo (1.4/1.5 already cover it).
- Part 6's `adk deploy cloud_run` traps (`--log_level` feeds gcloud verbosity, agent-folder `requirements.txt`, `--otel_to_cloud` boot crash, exits 0 on failure). See decision 3.

Renumbering after the merge: OTel → **Part 5**, Agent Runtime → **Part 6**, How to choose → **Part 7**.

## Decisions to settle before executing

| # | Decision | Recommendation |
|---|---|---|
| 1 | One server file or two? Today `06_custom_server.py` (plain console + JSON telemetry) and `07_cloudrun_json.py` (JSON everywhere + trace) are separate. | **Merge into `06_custom_server.py`**: JSON formatter with `severity`/`trace` on every handler, `TruncateFilter` kept, trace middleware on `/chat`. Delete `07`. "The thing you ran locally is the thing you ship" is the whole point of the merge. |
| 2 | Keep the Part 4 Cloud Run Job deploy of the plugin script? | **Drop it.** Fewer deploys, and 4.3 shows the identical query on the service. Keep `deploy_plugin_job.sh` since Part 3 still uses it. |
| 3 | Where do the `adk deploy cloud_run` traps go? Nothing uses that command after this change. | **Short "If you use `adk deploy cloud_run` instead" note in the How-to-choose part.** They are real traps worth keeping, but not in the main path. |
| 4 | Move "Callback or plugin?" to the end (4.4) or leave it between plugin and server? | **Move to end.** Keeps build → build → deploy uninterrupted. |
| 5 | Rename `04-production.md`? | **Keep the filename**, change the title. Avoids link churn. |

## Steps

### A. Code and deploy assets

- [ ] `examples/06_custom_server.py`: fold in `07`'s `CloudRunJsonFormatter`, `current_trace` ContextVar, `parse_trace_id`, and the `/chat` set/reset. `dictConfig` uses the JSON formatter on both handlers. Update docstring (run command with the trace header, port 8080).
  → verify: run locally, curl with `X-Cloud-Trace-Context`, all three line types carry `logging.googleapis.com/trace`.
- [ ] Delete `examples/07_cloudrun_json.py`.
- [ ] `deploy/Dockerfile`: `COPY`/`CMD` → `06_custom_server.py`; header comment.
- [ ] `deploy/deploy_cloudrun.sh`: rewrite to the `deploy_api.sh` pattern (`cp deploy/Dockerfile ./Dockerfile` + `trap`, `gcloud run deploy --source=. --allow-unauthenticated --set-env-vars=...`). Drop `adk deploy cloud_run`, `--otel_to_cloud`, the Option A/B comments, and the "adk deploy exits 0" workaround (`gcloud run deploy` fails properly). Keep the `Ready` check and smoke test, pointed at `POST /chat`.
  → verify: `bash -n`; then a real deploy (step C).

### B. Tutorial text

- [ ] `tutorial/04-production.md`: rewrite per the table above. Reuse existing prose and the two Part 6 Mermaid diagrams; new prose only for 4.3.
- [ ] `git rm tutorial/05-custom-server.md tutorial/06-cloud-run.md`.
- [ ] `git mv` `07-otel.md → 05-otel.md`, `08-agent-runtime.md → 06-agent-runtime.md`, `09-how-to-choose.md → 07-how-to-choose.md`. Update `# Part N` titles and prev/next nav in each.
- [ ] Add the `adk deploy cloud_run` traps note to `07-how-to-choose.md` (decision 3).

### C. Run the deploy and capture real output

The tutorial promises every output block is from a real run, and the current
verification status says the containerized deploy was never verified.

- [ ] `./deploy/deploy_cloudrun.sh`, curl `/chat`, run the three `gcloud logging read` queries (severity column, `jsonPayload.event="tool_end"` table, `trace=` filter). Paste real output into 4.3.
  → verify: severity column reads `INFO` (not blank); trace filter returns app + plugin + `google_adk` lines together.
- [ ] Tear down; record the teardown command in 4.3.

### D. Cross-references

Renumber `Part 5/6/7/8` → `4/4/5/6`, fix filenames, and drop references to deleted content:

| File | Lines |
|---|---|
| `TUTORIAL.md` | 66–71 (contents table) |
| `README.md` | 29–33 (examples table), 47 ("02 to 08") |
| `tutorial/01a-log-levels-local.md` | 171 (Part 5 → 4) |
| `tutorial/01b-log-levels-cloud.md` | 15, 97, 202, 361 (Part 6 → 4) |
| `tutorial/03-plugins.md` | nav only (Part 4 refs still valid) |
| `tutorial/05-otel.md` (was 07) | 85 nav |
| `tutorial/06-agent-runtime.md` (was 08) | 37 (Part 6 → 4), 44 (Part 7 → 5), 48 nav |
| `tutorial/07-how-to-choose.md` (was 09) | 15–22 table, 45, 63–64, 82, 88–90 (verification status: mark the deploy verified), 113 nav |
| `deploy/deploy_job.sh` | 55 (Part 6 → 4) |
| `examples/09_min_api.py` | 15 ("Part 5 onward" → "Part 4 onward") |

→ verify: `grep -rn -E 'Part [5-9]|0[5-9]-[a-z-]+\.md|07_cloudrun' ai/adk/logging` returns only intended hits.

### E. Housekeeping

- [ ] `ai/adk/logging/The` is an empty untracked file (stray shell redirect?). Delete if you agree.
- [ ] Working tree already has unrelated edits in `deploy_byoc.sh`, `agent.py`, `deploy_agent_engine.sh`, `01b`, `08`, `09`. This plan builds on top of them; commit or stash first so the merge is its own commit.
