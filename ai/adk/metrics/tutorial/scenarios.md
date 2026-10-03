[← 0 · Setup](00-setup.md)<br>
[→ Part 1 · What a metric is](part-1/index.md)<br>
[Tutorial index](../TUTORIAL.md)

---

# Scenarios

*The controlled experiments every page runs. One scenario per lesson.*

> [!NOTE]
> **Why you are here.** This is the spine of the tutorial. Each page names one
> scenario from the table below and one question it answers. You run the same
> agent every time and change exactly one condition, so the number that moves is
> the lesson.

Part 1 runs a scenario as a short script. From Part 2 on, you run it under load
with `load/turns.sh <scenario> [N]`, which fires N turns of the named scenario
against a running server. `workflow` runs as a script
([1.5](part-1/1.5-workflow-grain-metrics.md)). `export-outage` runs the
`baseline` scenario against a deliberately misconfigured server
([2.1](part-2/2.1-adk-web-otel-to-cloud.md)). The scenario name only selects what
`load/turns.sh` sends. It is never recorded as a metric attribute.

## The scenarios

| Scenario | Controlled change | Observation to capture | Operational question |
|---|---|---|---|
| `baseline` | One London turn per fresh session; N of them under load | The six histograms; per turn, two model calls, one tool call, tokens split by type | What does one successful turn cost in time, calls, and tokens? |
| `unknown-city` | Half the turns ask for Atlantis; `get_weather` returns an error status and does not raise | `execute_tool.duration` gains a second series carrying `error.type`; `invoke_agent.duration` gains none | Did a dependency failure become a user-visible failure? |
| `slow-tool` | Turns ask for a forecast, so `get_forecast` (a 0.3–1.5 s sleep) runs, mixed with London weather turns | Two tool-latency distributions; `invoke_agent.duration` rises with the tool, `client.operation.duration` does not | Is the dependency responsible for the slowdown? |
| `multi-city` | One turn in four names three cities in a single prompt | `tool_calls` and `inference_calls` per invocation split into two populations; the three-city turns carry the tokens and the duration | Is repeated work driving latency and consumption? |
| `growing-context` | N turns in one session instead of N fresh sessions | Input tokens per model call climb across the session; output tokens stay flat | Does accumulated context explain token growth? |
| `concurrent` | `slow-tool` and `baseline` turns fired in parallel instead of in sequence | Per-tool and per-turn durations match the sequential runs | Do overlapping turns contaminate each other's timers? |
| `export-outage` | The server starts without its resource labels, so Cloud Monitoring rejects every batch with a `400`; `baseline` turns against it | Every turn answers; one 400 per batch in the log; no new points; the restart discards the process totals | Is the agent healthy while telemetry is incomplete? |
| `workflow` | The two-agent `SequentialAgent` variant (planner → weather), one London turn | `invoke_agent.duration` splits by agent name; the outer agent's duration includes the durations of its sub-agents | Which numbers belong to the outer agent and which to the agent inside it? |

All scenarios drive the one shared agent that
[Setup](00-setup.md#meet-the-agent) introduces.

---

[← 0 · Setup](00-setup.md)<br>
[→ Part 1 · What a metric is](part-1/index.md)<br>
[Tutorial index](../TUTORIAL.md)
