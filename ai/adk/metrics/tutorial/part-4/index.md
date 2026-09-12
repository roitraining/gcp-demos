[← 3.7 · Task outcome](../part-3/3.7-task-outcome.md)<br>
[→ 4.1 · One line, one table](4.1-one-line-one-table.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 4 · Consume — rows in BigQuery

*The questions a histogram cannot answer: which session, which prompt, at what cost.*

> [!NOTE]
> **Why you are here.** A metric is aggregated and its attributes are bounded, so
> it can never name the one session that ran up the bill or show the prompt that
> caused it. This part records one row per lifecycle event in BigQuery, where an
> unbounded id and the full content belong.

Parts 1 through 3 traded detail for cheapness: a histogram folds many turns into
`count`, `sum`, and buckets, and [1.3](../part-1/1.3-attributes-and-cardinality.md)
showed why a session id can never be an attribute. That is the right trade for
"how slow, how many, how often, how much" in near real time, and the wrong store
for "which session, which prompt, at what cost". `BigQueryAgentAnalyticsPlugin`
writes one row per event, with ids, content, per-call tokens, and latency. You add
the plugin once and query with SQL from then on.

## In this part

| Section | Scenario | Question it answers |
|---|---|---|
| [4.1 · One line, one table](4.1-one-line-one-table.md) | `baseline` | What does one turn look like as rows? |
| [4.2 · Tokens, latency, cache per call](4.2-tokens-latency-cache-per-call.md) | `growing-context` | Which call was expensive, and was any of it cached? |
| [4.3 · Cost per session and per user](4.3-cost-per-session-and-user.md) | `multi-city` | Which session and which prompt cost the most? |
| [4.4 · The SDK](4.4-the-sdk.md) | `unknown-city` | What happened inside one invocation, step by step? |
| [4.5 · The Looker Studio template](4.5-looker-studio-template.md) | — | Can a reader without SQL see the same answers? |
| [4.6 · Metrics or rows](4.6-metrics-or-rows.md) | — | Which store answers which question? |

---

[← 3.7 · Task outcome](../part-3/3.7-task-outcome.md)<br>
[→ 4.1 · One line, one table](4.1-one-line-one-table.md)<br>
[Tutorial index](../../TUTORIAL.md)
