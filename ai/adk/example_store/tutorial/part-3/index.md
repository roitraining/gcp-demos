[← 2.2 · Search the store](../part-2/2.2-search-the-store.md)<br>
[→ 3.1 · Add ExampleTool](3.1-add-exampletool.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 3 · Attach the store to the agent

*Give the agent the store, ask the same four questions, and see what changes.*

> [!NOTE]
> **Why you are here.** Part 2 showed what the store returns. This part shows
> what the agent does with it: one added tool, and the replies from Part 1
> come back the way the store wants.

The agent gets the examples through `ExampleTool`. Despite the name, the model
never calls it. Before each model call, ADK runs the tool's request step,
which searches the store and adds the matches to the system instruction.

## In this part

| Section | What it covers |
|---|---|
| [3.1 · Add ExampleTool](3.1-add-exampletool.md) | The one-line change, the four questions again, and what Gemini receives. |
| [3.2 · When retrieval runs](3.2-when-retrieval-runs.md) | A search per model call, on the latest message only; then delete the store. |

---

[← 2.2 · Search the store](../part-2/2.2-search-the-store.md)<br>
[→ 3.1 · Add ExampleTool](3.1-add-exampletool.md)<br>
[Tutorial index](../../TUTORIAL.md)
