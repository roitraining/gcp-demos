[← 2.6 · Other backends](../part-2/2.6-other-backends.md)<br>
[→ 3.1 · Latency, three grains](3.1-latency-three-grains.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 3 · Consume: signals from histograms

*Turn the series in Cloud Monitoring into answers, dashboards, and an alert.*

> [!NOTE]
> **Why you are here.** The metrics are landing in Cloud Monitoring (Part 2), and
> now you read them: four operational questions from the six histograms, then one
> no framework metric can answer.

How slow, how many, how often failing, and how much each map to a PromQL signal;
3.5 puts them on a dashboard and 3.6 turns one into an alert. 3.7 adds a custom
counter for whether the task got done. Every page runs one scenario from
[scenarios.md](../scenarios.md) against a server it starts under its own
`OTEL_SERVICE_NAME`, such as `adk-metrics-3-2`. That name becomes the `job`
label every query on the page filters on, so pages run back to back with no wait
between them.

Queries read a `[10m]` window, so it still holds the page's load a minute after
the load ends. A per-minute rate averages over all 10 minutes, including the
quiet ones: 30 turns sent in 3 minutes read as 3 turns per minute, not 10.
Ratios and percentiles are unaffected.

## In this part

| Section | Scenario | Question it answers |
|---|---|---|
| [3.1 · Latency, three grains](3.1-latency-three-grains.md) | `slow-tool` | Is the dependency responsible for the slowdown? |
| [3.2 · Volume and shape](3.2-volume-and-shape.md) | `multi-city` | Is repeated work driving latency and consumption? |
| [3.3 · Errors](3.3-errors.md) | `unknown-city` | Did a dependency failure become a user-visible failure? |
| [3.4 · Tokens and cost](3.4-tokens-and-cost.md) | `growing-context` | Does accumulated context explain token growth? |
| [3.5 · A dashboard](3.5-a-dashboard.md) | `baseline` | Can I answer the four questions without writing a query? |
| [3.6 · An alert](3.6-an-alert.md) | `unknown-city` | Would this have paged me? |
| [3.7 · Task outcome](3.7-task-outcome.md) | `unknown-city` | Did execution complete without accomplishing the task? |

---

[← 2.6 · Other backends](../part-2/2.6-other-backends.md)<br>
[→ 3.1 · Latency, three grains](3.1-latency-three-grains.md)<br>
[Tutorial index](../../TUTORIAL.md)
