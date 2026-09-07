[← 0 · Setup](../00-setup.md)<br>
[→ 1.1 · Your first datapoint](1.1-your-first-datapoint.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 1 · What a metric is

*Run the agent locally and read the numbers it records, before any cloud is involved.*

> [!NOTE]
> **Why you are here.** Before you ship metrics anywhere, you need to know what
> ADK records, when, and what one datapoint contains. This part answers that on
> your laptop, with a console reader and no Google Cloud account.

A metric in ADK is a number recorded into a histogram at one of three moments,
tagged with a handful of attributes, and aggregated in the process before you
ever see it. Nothing prints on its own: with no reader installed, every
recording is discarded. Each page here installs a console reader, runs one
scenario from [scenarios.md](../scenarios.md), and reads the result.

## In this part

| Section | Scenario | Question it answers |
|---|---|---|
| [1.1 · Your first datapoint](1.1-your-first-datapoint.md) | `baseline` | Is the agent recording anything, and what did one turn cost? |
| [1.2 · Reading a histogram](1.2-reading-a-histogram.md) | `baseline` | Why record durations and tokens as histograms, not totals? |
| [1.3 · Attributes and cardinality](1.3-attributes-and-cardinality.md) | `unknown-city` | Which tool is failing, and can the metric say for whom? |
| [1.4 · The experimental family](1.4-the-experimental-family.md) | `baseline` | How many tokens did the whole turn use, not just each model call? |
| [1.5 · Workflow-grain metrics](1.5-workflow-grain-metrics.md) | `workflow` | Which numbers belong to the workflow and which to the agent inside it? |

---

[← 0 · Setup](../00-setup.md)<br>
[→ 1.1 · Your first datapoint](1.1-your-first-datapoint.md)<br>
[Tutorial index](../../TUTORIAL.md)
