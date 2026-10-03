# ADK logging tutorial

## Governing model

An ADK agent process produces **four log streams**: (1) your code, (2) the
`google_adk` framework, (3) the uvicorn web server (`uvicorn.access`), and (4)
OpenTelemetry telemetry. Most logging confusion is "configured one stream,
expected it to cover another." Keep new content consistent with this framing and
its numbering.

## Facts that are easy to get wrong (google-adk 2.8.0)

- The model runs in `global` while services run in `us-central1`. Set
  `GOOGLE_CLOUD_LOCATION` as a real Cloud Run env var: a copied `.env` loses to
  the environment ADK re-applies on top.
- ADK's servers load the first `.env` found walking up from the agent folder, so
  `demo_agent/` has no `.env` of its own; the Agent Runtime deploy scripts write
  one temporarily and remove it.
- `opentelemetry-exporter-gcp-logging` ships only pre-releases; it stays pinned
  to an exact version so pip installs it without `--pre`.

## Conventions

- Deploy scripts in `deploy/` use `set -euo pipefail`, read `PROJECT_ID` and
  `REGION` from the environment, copy their `deploy/Dockerfile*` to
  `./Dockerfile` with a cleanup `trap`, and smoke-test the result (a ready
  service can still return 500).
- The repeated prompt is "What's the weather in Tokyo?" in Parts 1 and 4, and
  "What's the weather in London?" in Parts 3, 5 and 6.
- Captured output comes from `jwd-gcp-demos`, which has a Model Armor floor
  setting that sanitizes every Gemini call. New captures belong on a project
  without one, such as `jwd-dev-5`.
- A claim that can't be verified yet goes in the Verification status section of
  `tutorial/how-to-choose.md`, never in faked output.
- Content knobs belong on 5.6 and other backends on 5.7; point there before
  writing a new deep dive on either.
