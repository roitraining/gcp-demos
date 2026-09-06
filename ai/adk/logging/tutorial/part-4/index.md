[← 3.5 · Plugin or level dial?](../part-3/3.5-plugin-or-level.md)<br>
[→ 4.1 · The structured plugin](4.1-structured-plugin.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 4 · Structured logging

*A JSON plugin, a custom server that owns all four streams, and the same server
shipped to Cloud Run with first-class severity and per-request trace grouping.*

> [!NOTE]
> **Why you are here.** You want Part 3's visibility for a running service you
> can query, alert on, and correlate. That rules out `LoggingPlugin` (it prints)
> and DEBUG (unstructured text). This part builds a plugin that emits structured
> `logging` records, a server where one config owns every stream, and that
> server on Cloud Run.

## In this part

| Section | What it covers |
|---|---|
| [4.1 · The structured plugin](4.1-structured-plugin.md) | A plugin whose callbacks emit machine-readable JSON events. |
| [4.2 · A custom server that owns all four streams](4.2-custom-server.md) | A hand-written server that configures every stream in one place. |
| [4.3 · The same server on Cloud Run](4.3-server-cloud-run.md) | Shipping that server so JSON becomes queryable log entries. |
| [4.4 · Callback or plugin?](4.4-callback-or-plugin.md) | Choosing between a plugin and a per-agent callback. |

---

[← 3.5 · Plugin or level dial?](../part-3/3.5-plugin-or-level.md)<br>
[→ 4.1 · The structured plugin](4.1-structured-plugin.md)<br>
[Tutorial index](../../TUTORIAL.md)
