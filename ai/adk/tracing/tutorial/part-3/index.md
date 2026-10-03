[← 2.6 · Other backends](../part-2/2.6-other-backends.md)<br>
[→ 3.1 · The free join](3.1-the-free-join.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 3 · Correlate

*Get every log line of a request to show up inside the right span.*

> [!NOTE]
> **Why you are here.** The tree is in Cloud Trace, but most of your logs are
> not in it. This part joins them: two fields on a log entry put it under its
> span, and each page brings one more log stream into the join.

A log entry that carries a `trace` and a `spanId` matching a stored span shows
up under that span in the Trace Explorer. ADK's `gen_ai.*` events carry both for
free. Your logs and the framework's need a bridge: a logging handler that copies
the current span's ids onto each log record. The request log needs
propagation.

```mermaid
flowchart LR
  subgraph streams["log streams"]
    a["gen_ai.* events<br/>stamped by default"]
    b["your logger.info"]
    c["google_adk"]
    d["Cloud Run request_log"]
  end
  a --> J{{"trace + spanId<br/>match a span?"}}
  b -->|"bridge (3.2)"| J
  c -->|"same bridge (3.3)"| J
  d -->|"propagation (3.4)"| J
  J -->|yes| span["under its span in Trace Explorer"]
```

*Four streams, one join. Each page below brings one more stream in.*

## In this part

| Section | Scenario | Question it answers |
|---|---|---|
| [3.1 · The free join](3.1-the-free-join.md) | `baseline` | Where are the model's messages in the trace? |
| [3.2 · Your tool's log line is missing](3.2-your-tools-log-line.md) | `classified-error` | Why is the tool's warning not in the trace? |
| [3.3 · Framework and server logs](3.3-framework-and-server-logs.md) | `slow-tool`, `concurrent` | Do the logs I did not write land in the right spans? |
| [3.4 · One trace per request](3.4-one-trace-per-request.md) | `tagged-request`, `unsampled-parent` | Is this trace the one my user's request produced? |
| [3.5 · Three ways to stamp](3.5-three-ways-to-stamp.md) | — | Which bridge do I use where? |

---

[← 2.6 · Other backends](../part-2/2.6-other-backends.md)<br>
[→ 3.1 · The free join](3.1-the-free-join.md)<br>
[Tutorial index](../../TUTORIAL.md)
