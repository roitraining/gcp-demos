# ADK metrics tutorial

## Governing model

A metric is a number recorded into a histogram at one of three moments (a model
call ends, a tool call ends, an agent invocation ends), tagged with a few
attributes, and aggregated before you see it. Every page names one scenario from
`tutorial/scenarios.md` and one operational question; a page that can't name a
question should be cut or merged.

## Facts that are easy to get wrong (google-adk 2.8.0)

- A single agent emits **six** metric names. `gen_ai.invoke_workflow.duration`
  needs the `Workflow` primitive; a `SequentialAgent` is measured on
  `invoke_agent.duration` (page 1.5).
- `error.type` is not free. A tool returning `{"status": "error"}` doesn't stamp
  it; the demo's `StatusAwareTool` maps that status to
  `error.type="lookup_failed"`.
- ADK's `MeterProvider` doesn't flush on exit, so scripts call `flush_metrics()`
  from `examples/_common.py`.
- `adk.experimental.*` metrics are off unless `ADK_EXPERIMENTAL_TELEMETRY` is set
  (page 1.4).
- A standalone script's cloud export needs `gcp.project_id` in
  `OTEL_RESOURCE_ATTRIBUTES`; `adk web --otel_to_cloud` injects it.
- Cloud Monitoring PromQL reads dotted histograms in the UTF-8 brace form with a
  suffix, such as `{"gen_ai.client.token.usage_sum"}`. The bare dotted name
  returns nothing.

## Conventions

- Each Part 3 page starts its server with `OTEL_SERVICE_NAME=adk-metrics-3-N`
  (3.1's concurrent deep dive uses `adk-metrics-3-1c`), and every query on the
  page filters on that `job`. Pages never wait for each other. Part 2 queries
  filter on their own server's job too.
- Read queries use `[10m]` windows. Only the 3.6 alert is short: `[1m]` rate,
  60 s hold, 30 s evaluation.
- The task-outcome counter (3.7) is gated behind `TUTORIAL_OUTCOME_METRIC`, so
  Parts 1 and 2 show only the six framework metrics.
- New captures use `jwd-dev-5`. `jwd-gcp-demos` has a Model Armor floor setting
  that adds model latency a reader's project won't have; pages captured before
  2026-10-03 still quote it. Save run records under `verification/`.
- The repeated prompt is "What's the weather in London?"; volume comes from
  `load/turns.sh <scenario> [N]`.
