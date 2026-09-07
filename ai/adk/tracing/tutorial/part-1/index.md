[← 0 · Setup](../00-setup.md)<br>
[→ 1.1 · The tree you already have](1.1-the-tree-you-already-have.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 1 · What a trace is

*Run the agent locally and read the span tree it opens, before any cloud is involved.*

> [!NOTE]
> **Why you are here.** Before you ship a trace anywhere, you need to know what
> ADK opens, when, and what one span contains. This part answers that on your
> laptop, with a console exporter and no Google Cloud account.

A trace is the tree of spans ADK opens around one turn. ADK opens them for you:
you do not add tracing, you install a reader and watch the tree that is already
there. Nothing leaves the process on its own, and with no provider installed
every span is dropped. Each page here runs one scenario from
[scenarios.md](../scenarios.md) and reads the result.

## In this part

| Section | Scenario | Question it answers |
|---|---|---|
| [1.1 · The tree you already have](1.1-the-tree-you-already-have.md) | `baseline`, `slow-tool` | What does one turn look like as a tree? |
| [1.2 · The raw span](1.2-the-raw-span.md) | `baseline` | What is a span made of? |
| [1.3 · Attributes and content](1.3-attributes-and-content.md) | `content-off` | What is on a span, and who can read it? |
| [1.4 · An error turn, three ways](1.4-an-error-turn-three-ways.md) | `returned-error`, `classified-error` | Which step failed, and how would I know? |
| [1.5 · A trace per turn, a session across traces](1.5-a-trace-per-turn.md) | `multi-turn` | How do I see a whole conversation? |
| [1.6 · Your own span inside a tool](1.6-your-own-span-inside-a-tool.md) | `custom-span` | Where inside my tool did the time go? |

---

[← 0 · Setup](../00-setup.md)<br>
[→ 1.1 · The tree you already have](1.1-the-tree-you-already-have.md)<br>
[Tutorial index](../../TUTORIAL.md)
