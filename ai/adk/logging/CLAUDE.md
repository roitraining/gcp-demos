# ADK logging tutorial — conventions

Scope: the tutorial under `ai/adk/logging/`. Applies when editing the tutorial
docs, examples, or deploy scripts here.

Page anatomy, nav, code-block labels, callouts, deep dives, and voice follow
the `tutorial-style` skill in `.claude/skills/tutorial-style/`. Load it first.
This file holds only what is specific to this tutorial.

## Layout

- `TUTORIAL.md` is the index. `tutorial/00-setup.md` is page 0.
  `tutorial/part-N/index.md` is each multi-page part's landing page; Part 2
  and the final page (`tutorial/how-to-choose.md`) are single pages that are
  their own landing. Subtask pages are `tutorial/part-N/N.M-slug.md`.
- The linear thread runs index → 00-setup → part-1/index → 1.1 … →
  part-2/index → part-3/index → 3.1 … → how-to-choose.
- Links to shared assets (`examples/`, `deploy/`, `otel/`, `demo_agent/`,
  `agent_runtime_byoc/`) are `../../` from a `part-N/` page, but `../` from
  `00-setup.md` and `how-to-choose.md`, which sit at `tutorial/` root.
- Every code and console block is captured from a real run against a real GCP
  project. If a block can't be verified yet, say so in the Verification status
  section of `tutorial/how-to-choose.md` rather than faking it.

## The four-streams framing

The whole tutorial rests on one model: an ADK agent process produces **four log
streams** — (1) your code, (2) the `google_adk` framework, (3) the uvicorn web
server (`uvicorn.access`), (4) OpenTelemetry telemetry. Most logging confusion is
"configured one stream, expected it to cover another." Keep new content consistent
with this framing and the stream numbering.

## Examples and deploy scripts

- Examples live in `examples/NN_name.py`; the shared agent is `demo_agent/`, shared
  helpers are `examples/_common.py`.
- Deploy scripts in `deploy/` are `set -euo pipefail`, take `PROJECT_ID`/`REGION`
  from the env, copy the matching `deploy/Dockerfile*` to `./Dockerfile` with a
  cleanup `trap`, and smoke-test the result (a ready service can still 500).
- The model region is `global` while services run in `us-central1`; set
  `GOOGLE_CLOUD_LOCATION` as a real Cloud Run env var, since a copied `.env` loses
  to the environment ADK re-applies on top.

## Tutorial-specific conventions

- The repeated prompt is "What's the weather in Tokyo?" in Parts 1 and 4, and
  "What's the weather in London?" in Parts 3, 5, and 6. Later steps on a page
  say "ask the London question in a new session."
- Point at 5.6 for content knobs and 5.7 for other backends before writing a
  new deep dive on either.
