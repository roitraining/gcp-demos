[← Part 1 · The agent without examples](../part-1/index.md)<br>
[→ 2.1 · Load the examples](2.1-load-the-examples.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 2 · Fill and search the store

*Load eight examples into the store, then search it the way ADK will.*

> [!NOTE]
> **Why you are here.** The agent can only follow examples the store returns.
> This part fills the store and shows which examples come back for each
> question, before any agent is involved.

An example is a short conversation: a user message and the steps the model
should take in reply, including any tool call. The store turns each example's
search key into an embedding, a list of numbers that places similar text close
together. A search embeds the question the same way and returns the nearest
examples with a similarity score.

## In this part

| Section | What it covers |
|---|---|
| [2.1 · Load the examples](2.1-load-the-examples.md) | What one example contains, and loading two per intent. |
| [2.2 · Search the store](2.2-search-the-store.md) | Scores for each of the four questions, and the 0.5 cutoff ADK applies. |

---

[← Part 1 · The agent without examples](../part-1/index.md)<br>
[→ 2.1 · Load the examples](2.1-load-the-examples.md)<br>
[Tutorial index](../../TUTORIAL.md)
