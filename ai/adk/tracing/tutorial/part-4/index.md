[← 3.5 · Three ways to stamp](../part-3/3.5-three-ways-to-stamp.md)<br>
[→ 4.1 · The slow step](4.1-the-slow-step.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 4 · Consume

*Answer the on-call questions from the trees and logs you now collect.*

> [!NOTE]
> **Why you are here.** Every turn now lands in Cloud Trace with its logs inside
> its spans. This part uses that to answer the questions an on-call alert
> raises.

Each question has one Trace Explorer surface that answers it:

| On-call question | Trace Explorer surface |
|---|---|
| Which step was slow? | The **Span duration** chart and the **Grouped** tab by span name, then one slow trace's waterfall |
| What did this user's request do? | **Add attribute filter** on `gen_ai.conversation.id`, or **Search for trace** by id |
| Which step failed, and what did it say? | **Span status** error, the red bar, and the tool's log line in **Logs & Events** |

## In this part

| Section | What it covers |
|---|---|
| [4.1 · The slow step](4.1-the-slow-step.md) | Find the span that makes a turn slow under load. |
| [4.2 · One user's request](4.2-one-users-request.md) | Pull one conversation's turns and read what each one did. |
| [4.3 · The failed step](4.3-the-failed-step.md) | Find the red span, its `error.type`, and the log line beside it. |
| [4.4 · Traces, logs, metrics, rows](4.4-traces-logs-metrics-rows.md) | Which store answers which question, and the ids that join them. |
| [4.5 · Cost, retention, and content policy](4.5-cost-retention-content.md) | What tracing costs, how long it lasts, and what stays out of a span. |

---

[← 3.5 · Three ways to stamp](../part-3/3.5-three-ways-to-stamp.md)<br>
[→ 4.1 · The slow step](4.1-the-slow-step.md)<br>
[Tutorial index](../../TUTORIAL.md)
