[← 2.6 · Other backends](../part-2/2.6-other-backends.md)<br>
[→ 3.1 · Latency, three grains](3.1-latency-three-grains.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 3 · Consume — signals from histograms

*Turn the series in Cloud Monitoring into answers, dashboards, and an alert.*

> [!NOTE]
> **Why you are here.** The metrics are landing in Cloud Monitoring (Part 2).
> Now you read them. An operator asks four questions of a running agent, and this
> part answers each from the six histograms, then meets the one question no
> framework metric can answer.

The four questions, how slow, how many, how often failing, and how much, each map
to a signal you read off the histograms with PromQL: percentiles, rates, an
`error.type` ratio, and the token `sum`. Then 3.5 puts them on a dashboard and 3.6
turns one into an alert. The fifth question, did the task actually get done, is
the one no framework metric can answer; 3.7 adds the single custom instrument that
can. Every page runs one scenario from [scenarios.md](../scenarios.md) and reads
the result back from the cloud.

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
