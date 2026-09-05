# 5.5 redesign: your own minimal OTel server (local + Cloud Run)

Supersedes the earlier 5.5 (which was an `InMemoryRunner` fire-one-turn script).
Jeff's correction, 2026-09-05: the goal is a **minimal agent server you write
yourself** that installs the OTel exporters, tested **locally**, showing how the
content knob is set via `.env`, then **deployed to Cloud Run**.

## Why a server, not a script

5.1–5.4: the ADK CLI started the process, so it installed the exporters. In your
own server nothing does — so you make the two calls. `06_custom_server.py` (Part
4) is already that server minus telemetry; 5.5 is the same shape with OTel export
wired in.

## Key finding that shapes 5.5

**In your own server, `.env` carries ALL the OTel vars — endpoint and knobs.**
The 5.2 timing trap (endpoint vars must be shell exports, not `.env`) exists only
because the CLI builds exporters *before* it loads the agent's `.env`. A
hand-written server loads `.env` first (`_common.bootstrap` → `load_dotenv`,
`_common.py:49-55`), *then* builds the exporters, *then* runs turns. So order is
under your control and `.env` works for everything. Content knobs are read
per-turn anyway (`tracing.py:865-873`, `context.py:179-180`).

This is the teaching point: 5.2 forced shell exports; your own server does not.

## Example 08 — new shape: `08_otel_server.py` (rename from `08_otel_cloud.py`?)

A minimal FastAPI server = stripped `06_custom_server.py`:
- `bootstrap()` (loads `.env`) at top.
- The **two calls** before the Runner is built, in `lifespan` or module scope:
  ```python
  hooks = get_gcp_exporters(enable_cloud_logging=True)
  maybe_set_otel_providers([hooks])
  ```
- `App(root_agent=...)` + `Runner`, created once in `lifespan`.
- One `POST /chat` endpoint that runs a turn.
- `uvicorn.run(app, port=8080)`.
- **No** CloudRunJsonFormatter / trace-context / dictConfig from 06 — that is
  06's concern (streams 1–3). 08's only added concern is stream 4 (OTel export).

Resolved decisions (Jeff, 2026-09-05):
- **Rename** `08_otel_cloud.py` → `08_otel_server.py` (it's a server now). Touches
  README, TUTORIAL.md, 07, Dockerfile CMD, cross-refs.
- **Cloud Run knob** via `--set-env-vars`, NOT baked `.env` — matches the
  existing `deploy/Dockerfile` ("no .env in the image") + `deploy_cloudrun.sh`
  pattern. Teaching point: **local uses `.env`, Cloud Run uses `--set-env-vars`**
  — same knob, two delivery mechanisms.
- **Deploy** = inline commands (Dockerfile + `gcloud run deploy --source`), no
  wrapper script — consistent with the 5.4 inline decision.
- 08 uses a **bare** `/chat` request model, minimal and self-contained.

## 5.5 tutorial flow

1. **Why you are here** — CLI installed exporters for you; your server must.
2. **The two calls** — `get_gcp_exporters(enable_cloud_logging=True)` +
   `maybe_set_otel_providers([hooks])`, where they go (before the Runner).
   `.env` works for all OTel vars here (the timing callout, contrasting 5.2).
3. **Run locally** — start the server, curl `/chat`, read `gen_ai.*` back in
   Logs Explorer (Query editor, `logName=~"gen_ai\."`).
4. **The knob, via `.env`, before/after (local)** — `.env` has
   `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT`; curl → content
   `<elided>`. Change `.env` to `EVENT_ONLY`, restart the server, curl → content
   present. Demonstrates `.env`-driven config on your own server.
5. **Deploy to Cloud Run** — the same server, same `.env`, ships in the image.
   Needs a Dockerfile (08's own, or reuse the folder pattern) + `gcloud run
   deploy`. Read `gen_ai.*` back from Cloud Logging in the cloud. Teardown.

## Cloud Run deploy for 08 — the real work

06 is described as "Cloud Run-ready" but I have not confirmed a Dockerfile exists
for it. Options:
- [ ] Does `deploy/` already have a Dockerfile for a custom server (06)? If yes,
      reuse it. If no, 08 needs one (`deploy/Dockerfile.otel_server`?) +
      a deploy block or short script.
- The folder convention (CLAUDE.md): deploy scripts are `set -euo pipefail`, take
  `PROJECT_ID`/`REGION`, copy `deploy/Dockerfile*` → `./Dockerfile` with a
  cleanup trap, smoke-test. But Jeff just had me DELETE the 5.4 wrapper script in
  favor of inline commands. So 5.5's Cloud Run half should likely also be inline
  `docker build` / `gcloud run deploy` commands, not a script. **Confirm.**

## Verification

VERIFIED LOCALLY (Jeff's machine, 2026-09-05, project jwd-gcp-demos):
- [x] `08_otel_server.py` starts locally; `/chat` returns
      `{"response":"The weather in London is currently 15°C with drizzle."}`.
- [x] `gen_ai.*` events land in Cloud Logging from the local server run.
      Resource = `generic_task`, `resource.labels.job` = the `OTEL_SERVICE_NAME`
      value (`weather-agent`), `task_id=laptop-1`. NOTE: service name maps to
      **`resource.labels.job`**, not a `service.name` label — filter on that.
- [x] Content knob, live before/after:
      - `.env` `...CAPTURE_MESSAGE_CONTENT=true` → content present
        (`'text': 'What is the weather in London?'`, system prompt, tool call).
      - `...=NO_CONTENT` → `<elided>` on every entry.
- [ ] Cloud Run deploy of 08 reaches Ready, `/chat` works, `gen_ai.*` in Cloud
      Logging on the Cloud Run resource. **NEEDS-RUN** — deploy not yet run.

The `.env` in the tutorial venv already carries `...CAPTURE_MESSAGE_CONTENT=true`;
5.5's demo overrides to `NO_CONTENT` for the "off" state, or sets the .env line.

## Files touched

| File | Change |
|---|---|
| `examples/08_otel_cloud.py` | Rewritten as the minimal OTel **server** (maybe renamed). |
| `tutorial/05-otel.md` | 5.5 rewritten to the flow above; 5.6 unchanged. |
| `deploy/Dockerfile.*` | New, if none exists for a custom server. |
| `README.md`, `TUTORIAL.md` | Example 08 description; filename if renamed. |
| `07-how-to-choose.md` | Verification status for 5.5 local + Cloud Run runs. |
| `docs/adk-otel-rewrite.md` | Stage 4 note: 5.5 redesigned per this doc. |
