# ADK metrics tutorial — conventions

Scope: the tutorial under `ai/adk/metrics/`. Applies when editing the tutorial
docs, examples, or deploy scripts here.

Page anatomy, nav, code-block labels, callouts, deep dives, and voice follow the
`tutorial-style` skill in `.claude/skills/tutorial-style/`. Load it first. This
file holds only what is specific to this tutorial. The full plan, decisions, and
verification tables live in `docs/adk-metrics-tutorial.md` at the repo root.

## Layout

- `TUTORIAL.md` is the index. `tutorial/00-setup.md` is page 0.
  `tutorial/scenarios.md` is the scenario spine, linked from the index and every
  part landing page. `tutorial/part-N/index.md` is each part's landing page;
  subtask pages are `tutorial/part-N/N.M-slug.md`.
- The linear thread runs index → 00-setup → scenarios → part-1/index → 1.1 … →
  part-2/index → … → how-to-choose.
- Links to shared assets (`examples/`, `demo_agent/`, `queries/`, `load/`,
  `deploy/`) are `../../` from a `part-N/` page, but `../` from `00-setup.md`,
  `scenarios.md`, and `how-to-choose.md`, which sit at `tutorial/` root.

## The three-moments framing

The whole tutorial rests on one model: **a metric is a number recorded into a
histogram at one of three moments (a model call ends, a tool call ends, an agent
invocation ends), tagged with a few attributes, and aggregated before you see
it.** Keep new content consistent with this framing.

## Scenarios drive every page

Every page names one scenario from `tutorial/scenarios.md` and one operational
question. That pair becomes the page's **Why you are here** note. A page that
cannot name a question is a page to cut or merge. One scenario per lesson; a deep
dive may run one more.

## Verified facts specific to this build (google-adk 2.8.0)

- A **single agent emits six** metric names, not seven.
  `gen_ai.invoke_workflow.duration` needs the newer `Workflow` primitive; a
  `SequentialAgent` is measured as an outer agent on `invoke_agent.duration`
  (see 1.5).
- **`error.type` is not free.** A plain function returning `{"status": "error"}`
  does not stamp it. The demo wraps tools in `StatusAwareTool(FunctionTool)`,
  which overrides `_detect_error_in_response` to map a failure status to
  `error.type="lookup_failed"`. A raising tool stamps it too but crashes the
  invocation.
- **Script export needs a flush.** ADK installs the `MeterProvider` with
  `shutdown_on_exit=False`, so example scripts call
  `metrics.get_meter_provider().force_flush()` (helper `flush_metrics()` in
  `examples/_common.py`).
- **`adk.experimental.*` is off by default**, gated on
  `ADK_EXPERIMENTAL_TELEMETRY` (see 1.4).
- **Raw script cloud export needs `gcp.project_id`** in
  `OTEL_RESOURCE_ATTRIBUTES`; `adk web --otel_to_cloud` injects it, a standalone
  script does not (Part 2).
- **Cloud Monitoring PromQL** addresses dotted histograms as suffixed series in
  the UTF-8 brace form: `{"gen_ai.client.token.usage_sum"}`, `..._count`,
  `..._bucket`. The native form returns nothing (Part 3).

## Examples

- Examples live in `examples/NN_name.py`; the shared agent is `demo_agent/`,
  shared helpers are `examples/_common.py`.
- Every console block on a page is captured from a real run against
  `jwd-gcp-demos`. Token counts vary run to run (a real model), so quote them as
  representative, not exact. Save the run record under `verification/`.
- `install_console_reader()` writes its JSON to a file (default `out/metrics.json`)
  rather than the console, since a full dump is too long to read in a terminal;
  pages tell the reader to open it (`code out/metrics.json` in VS Code). The
  `out/` folder is gitignored.

## Tutorial-specific conventions

- The repeated prompt is "What's the weather in London?" for single turns;
  `load/turns.sh <scenario> [N]` for volume.
- The custom task-outcome counter (page 3.7) is gated behind
  `TUTORIAL_OUTCOME_METRIC` so Parts 1 and 2 show exactly the six framework
  metrics.
