[→ 5.0 · What stream 4 is](5.0-what-stream-4-is.md)<br>
[← 4.4 · Callback or plugin?](../part-4/4.4-callback-or-plugin.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 5 · OpenTelemetry

*Stream 4 — the spans ADK already emits with nothing configured, and where they
go once you point them at Google Cloud.*

> [!NOTE]
> **Why you are here.** Parts 1-4 were all the `logging` module: streams 1, 2 and 3,
> text you read a line at a time or query a field at a time. Stream 4 is different
> machinery. ADK emits **OpenTelemetry** spans, GenAI log events, and metrics, and
> none of them print. They leave through an exporter. You want them because a span
> tree answers *where did the time go* and *what did each step actually receive*,
> which no flat log line can. The surprise this part opens with is that you do not
> configure anything to get them: `adk web` traces every turn already. What the
> flag in 5.2 adds is not tracing, it is **export**.

Part 5 starts from what is already running (5.0, 5.1), adds one flag to send it to
Google Cloud (5.2 onward), and only writes code in the one situation that needs it.

## In this part

| Section | What it covers |
|---|---|
| [5.0 · What stream 4 is](5.0-what-stream-4-is.md) | The three OTel signals, the five span names, and where they go |
| [5.1 · adk web is already tracing](5.1-adk-web-already-tracing.md) | Reading the span tree in the dev UI with nothing configured |
| [5.2 · OTel to Cloud](5.2-otel-to-cloud.md) | One flag, the `gen_ai.*` events in Cloud Logging, and the content knobs |
| [5.3 · adk api_server](5.3-api-server.md) | The same flag headless: curl in, Cloud Logging out |
| [5.4 · The same flag on Cloud Run](5.4-cloud-run.md) | `adk deploy cloud_run --otel_to_cloud` under a service account |
| [5.5 · Your own server](5.5-your-own-server.md) | Installing the Cloud exporters yourself in a hand-written server |
| [5.6 · The content knobs](5.6-content-knobs.md) | Reference for which knob governs which stream, and the safe values |
| [5.7 · Other backends](5.7-other-backends.md) | Pointing the same OTel machinery at any OTLP backend |
| [5.8 · How this relates to Parts 1-4](5.8-relates-to-parts-1-4.md) | One turn in four places, which join and which do not |

---

[→ 5.0 · What stream 4 is](5.0-what-stream-4-is.md)<br>
[← 4.4 · Callback or plugin?](../part-4/4.4-callback-or-plugin.md)<br>
[Tutorial index](../../TUTORIAL.md)
