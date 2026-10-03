[← 3.5 · Plugin or level dial?](../part-3/3.5-plugin-or-level.md)<br>
[→ 4.1 · The structured plugin](4.1-structured-plugin.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 4 · Structured logging

*A JSON plugin, a custom server that owns streams 1–3, and the same server
shipped to Cloud Run with first-class severity and per-request trace grouping.*

> [!NOTE]
> **Why you are here.** `LoggingPlugin` prints and DEBUG is plain text, so
> neither gives a running service logs you can query and alert on. This part
> builds a plugin that emits JSON records and runs it in your own server on
> Cloud Run.

## In this part

| Section | What it covers |
|---|---|
| [4.1 · The structured plugin](4.1-structured-plugin.md) | A plugin whose callbacks emit machine-readable JSON events. |
| [4.2 · A custom server that owns streams 1–3](4.2-custom-server.md) | A hand-written server that configures streams 1–3 in one place. |
| [4.3 · The same server on Cloud Run](4.3-server-cloud-run.md) | Shipping that server so JSON becomes queryable log entries. |
| [4.4 · Callback or plugin?](4.4-callback-or-plugin.md) | Choosing between a plugin and a per-agent callback. |

---

[← 3.5 · Plugin or level dial?](../part-3/3.5-plugin-or-level.md)<br>
[→ 4.1 · The structured plugin](4.1-structured-plugin.md)<br>
[Tutorial index](../../TUTORIAL.md)
