[← Setup](../00-setup.md)<br>
[→ Part 2 · Fill and search the store](../part-2/index.md)<br>
[Tutorial index](../../TUTORIAL.md)

---

# Part 1 · The agent without examples

*Run the order-support agent with no examples and see which replies need fixing.*

> [!NOTE]
> **Why you are here.** Before you add examples, you need a baseline: what the
> agent does with only an instruction and a tool. Nothing here needs the store,
> so do this while it is created.

The agent in [agents/no_examples/agent.py](../../agents/no_examples/agent.py)
has a one-line instruction and one tool. Both agents in this tutorial share
them from [agents/orders.py](../../agents/orders.py):

```python
INSTRUCTION = (
    "You are the order-support agent for an online store. Use"
    " get_order_status to look up an order."
)

def get_order_status(order_id: str) -> dict:
  """Looks up the status of an order by its four-digit order ID."""
```

The store has four kinds of request to handle, and wants a set reply for each:

| Intent | The reply the store wants |
|---|---|
| Order status | Look up the order, then one line: `Order 4417: shipped, arrives Tuesday.` |
| Missing order ID | Ask for the four-digit number; don't call the tool |
| Refund | One policy sentence pointing to the returns team; don't call the tool |
| Off-topic | One sentence steering back to orders |

The instruction says none of this. Part 3 teaches it with examples instead.

**Step 1 — Ask one question per intent.**

`adk run` with a query runs one turn and exits. The agent also logs a line
per model call saying whether that request carried any examples; see
[What prints the `[examples]` lines?](#what-prints-the-examples-lines)

**Command:**

```bash
.venv/bin/adk run agents/no_examples "Where is order 4417?"
.venv/bin/adk run agents/no_examples "Where's my order?"
.venv/bin/adk run agents/no_examples "I want a refund for order 5521."
.venv/bin/adk run agents/no_examples "What's a good recipe for pancakes?"
```

**Expected output:** trimmed to the agent's lines; the recipe is cut short.

```console
[examples] none in this request
[examples] none in this request
[order_support]: Order #4417 has been **shipped** and is estimated to arrive on **Tuesday**.

[examples] none in this request
[order_support]: Could you please provide your 4-digit order ID so I can look up the status for you?

[examples] none in this request
[examples] none in this request
[order_support]: Order 5521 is currently marked as **delivered**.
To proceed with your refund request, could you please let me know the reason for the refund (e.g., damaged item, wrong item, or dissatisfaction)? If applicable, providing any details or photos of the issue will help us process it as quickly as possible.

[examples] none in this request
[order_support]: Here is a simple, classic pancake recipe:
### Classic Pancakes
**Ingredients:**
* 1 ½ cups all-purpose flour
...
```

> [!IMPORTANT]
> **What it means.** Only one of the four replies is what the store wants.
>
> | Intent | What the agent did |
> |---|---|
> | Order status | Right facts, its own wording and bold markup |
> | Missing order ID | Asked for the ID: already right |
> | Refund | Called the tool, then invented a refund process |
> | Off-topic | Wrote the recipe |
>
> Two `[examples]` lines mean two model calls: one that asked for the tool,
> and one after the tool answered.

The missing-ID reply shows that the model already does some things well.
Examples matter for the behaviors it can't guess, such as your refund policy.
Part 2 loads examples for all four intents into the store.

## Deep dives

### What prints the `[examples]` lines?

`log_examples` in [agents/orders.py](../../agents/orders.py) is a
`before_model_callback`. ADK calls it just before each request goes to Gemini.
It looks for an `<EXAMPLES>` block in the request's system instruction and
prints the user line of each example it finds. This agent has no examples, so
it prints `none`. The same callback runs in Part 3, where the block is there.

### Why not write the rules into the instruction?

For four intents you could, and it would work. Examples pay off as the list
grows. An example shows the exact reply and tool-call sequence instead of
describing them. With a store, each request carries only the examples close
to the user's question, so the prompt stays small with hundreds of examples.

---

[← Setup](../00-setup.md)<br>
[→ Part 2 · Fill and search the store](../part-2/index.md)<br>
[Tutorial index](../../TUTORIAL.md)
