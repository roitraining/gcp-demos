# ADK logging tutorial — conventions

Scope: the tutorial under `ai/adk/logging/`. Applies when editing the tutorial
docs, examples, or deploy scripts here.

## Tutorial structure

- The tutorial is `TUTORIAL.md` (index) plus one file per part in `tutorial/`,
  named `NN-topic.md` (Part 1 is split into `01a`/`01b`). Each part opens with a
  `# Part N · Title` heading and a one-line italic subtitle, and ends with a
  `← Prev · Tutorial index · Next →` nav footer.
- Renumbering a part means renaming its file **and** fixing every cross-reference:
  nav footers, the `TUTORIAL.md` contents table, `README.md`, and inline
  `Part N` / `NN-topic.md` mentions elsewhere. Grep for both the number and the
  filename before considering it done.
- Every code and console block is captured from a **real run** against a real GCP
  project — do not invent output. If a block can't be verified yet, say so in the
  Verification status section of `07-how-to-choose.md` rather than faking it.

## Code-block labels

Every runnable command block is introduced by a bold **`**Command:**`** label on
its own line, and every result block by **`**Expected output**`** (optionally with
a trailing `— note` or `:`). This lets a reader tell at a glance which fences to
run versus read.

- A block already led by `**👉 Do this...**` or `**Step N — ...**` keeps that
  sentence, but drop its trailing colon and add `**Command:**` before the fence:

  ```
  **👉 Do this.** Deploy and run at INFO.

  **Command:**

  ```bash
  ...
  ```
  ```

- A block introduced by plain prose ending in a colon: change the colon to a
  period and add `**Command:**`.
- Do **not** label: code-shape snippets (illustrative Python classes/config),
  pipe fragments, browser-input blocks, or a second block paired under one
  lead-in.

## Bash formatting in code blocks

- One value per line for multi-flag commands: put each `--flag` on its own
  continuation line (`\`), keeping the first positional arg (e.g. a `gcloud
  logging read` query string) intact on its own line.
- Split `export VAR=x VAR2=y` into separate `export` statements, one per line.
- Leave alone: short single-line commands that already fit readably (e.g.
  `gcloud run ... delete ... --quiet` teardowns), env-prefix invocations
  (`SCRIPT=... ./deploy/...`, the vars must stay on the command line), and
  `curl` short flags (`-s -X -H`), which already wrap with `-d` on its own line.

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
