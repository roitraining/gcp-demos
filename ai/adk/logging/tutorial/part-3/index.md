[← Part 2 · Access logs](../part-2/index.md)<br>
[→ 3.1 · LoggingPlugin: one line to wire up](3.1-loggingplugin.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 3 · Plugins

*A clean, human-readable narration of the agent's steps:
`LoggingPlugin` and `DebugLoggingPlugin`, locally and on Cloud Run.*

> [!NOTE]
> **Why you are here.** INFO is too terse to debug a tool-calling problem and
> DEBUG dumps the whole conversation as raw JSON. ADK ships two plugins for the
> middle ground: which tool ran, with which arguments, what it returned, and what
> it cost.

## In this part

| Section | What it covers |
|---|---|
| [3.1 · LoggingPlugin](3.1-loggingplugin.md) | One line to wire up; how the lifecycle hooks print. |
| [3.2 · LoggingPlugin on Cloud Run](3.2-loggingplugin-cloud-run.md) | What the cloud does with a print-based plugin. |
| [3.3 · DebugLoggingPlugin](3.3-debugloggingplugin.md) | Capture one whole turn to a YAML file. |
| [3.4 · DebugLoggingPlugin on Cloud Run](3.4-debugloggingplugin-cloud-run.md) | File-writing plugin in an ephemeral container. |
| [3.5 · Plugin or level dial?](3.5-plugin-or-level.md) | When to reach for a plugin instead of the level. |

---

[← Part 2 · Access logs](../part-2/index.md)<br>
[→ 3.1 · LoggingPlugin: one line to wire up](3.1-loggingplugin.md)<br>
[Tutorial index](../../TUTORIAL.md)
