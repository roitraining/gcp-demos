# Plan: Example Store + ExampleTool tutorial

**Status:** draft, awaiting review. Not started.

## Goal

Build a runnable sample in which an ADK agent retrieves few-shot examples from a
Vertex AI Example Store on each turn, and show how the agent behaves with and
without them.

**Done when** a reader can start from an empty GCP project, run the agent, see
which examples each query retrieved, and delete everything afterward, using
only the files in the sample.

## Scenario

An order-support agent with one function tool, `get_order_status(order_id)`.
The stored examples teach behavior the model would not produce on its own:

| Intent | Example teaches |
|---|---|
| Order status | Call `get_order_status`, then reply in a fixed one-line format (`Order 4417: shipped, arrives Tue.`) |
| Missing order ID | Ask for the ID instead of guessing or calling the tool |
| Refund request | Reply with a fixed policy sentence and no tool call |
| Off-topic | Redirect to orders in one sentence |

Each intent should retrieve a different subset of examples, so the reader can
see retrieval change from query to query.

## Files

Location: `contributing/samples/tools/example_store/` (see open question 1).

| File | Purpose |
|---|---|
| `README.md` | The tutorial: prerequisites, steps, expected output, cleanup |
| `examples.py` | Example data used by `setup_store.py` |
| `setup_store.py` | Creates the store, upserts the examples, prints the store resource name |
| `agent.py` | Defines `root_agent` with `get_order_status` and `ExampleTool(VertexAiExampleStore(...))` |
| `cleanup.py` | Deletes the store |

## Architecture

```
 Local machine                                    Google Cloud (Vertex AI)
┌──────────────────────────────────────┐        ┌──────────────────────────────┐
│ setup_store.py   (run once)          │──(1)──▶│ Example Store                │
│   examples.py                        │ upsert │   stored examples            │
│                                      │        │   + embeddings               │
│ ADK agent        (adk run / adk web) │        │   (text-embedding-005)       │
│ ┌──────────────────────────────────┐ │        │                              │
│ │ root_agent (LlmAgent)            │ │        │                              │
│ │  ├─ get_order_status  (tool)     │ │        │                              │
│ │  └─ ExampleTool                  │ │        │                              │
│ │      └─ VertexAiExampleStore ────┼─┼──(2)──▶│                              │
│ │         (provider)               │ │ search └──────────────────────────────┘
│ └──────────────────────────────────┘ │
│                 │                    │        ┌──────────────────────────────┐
│                 └────────────────────┼──(3)──▶│ Gemini                       │
│                                      │generate└──────────────────────────────┘
└──────────────────────────────────────┘
```

| Flow | When | What happens |
|---|---|---|
| (1) upsert | Once, at setup | `setup_store.py` creates the store and loads the examples. The store embeds each example's search key. |
| (2) search | Every model call | `ExampleTool` passes the user's message to `VertexAiExampleStore`, which runs a similarity search and returns the matches. |
| (3) generate | Every model call | ADK adds the matches to the system instruction as an `<EXAMPLES>` block and sends the request to Gemini. |

The agent never calls `ExampleTool` the way it calls `get_order_status`.
`ExampleTool` only edits the request before ADK sends it.

## Decisions

| Decision | Choice | Reason |
|---|---|---|
| Store config | `text-embedding-005` in `us-central1` | Assumed; confirm in step 1 |
| Search key | The user utterance of each example | ADK searches with `search_key_generation_method: last_entry`, which matches against the stored `search_key` |
| Store name | `EXAMPLE_STORE_NAME` in `.env` | Keeps project IDs out of code |
| Retrieval logging | `before_model_callback` that prints the `<EXAMPLES>` block | Retrieval is otherwise invisible; a callback needs less setup than tracing |
| Comparison | README shows the same queries with `ExampleTool` removed | Shows the reader what the examples change |

## Steps

1. [ ] Check the Example Store API (`ExampleStore.create`, `ExampleStoreConfig`,
   the `upsert_examples` payload, `delete`) against the Vertex docs and the
   installed `google-cloud-aiplatform`.
   Verify: a minimal script runs against a real project.
2. [ ] Write `examples.py` with one or two examples per intent.
3. [ ] Write `setup_store.py`.
   Verify: it prints `projects/.../exampleStores/...`, and
   `VertexAiExampleStore(name).get_examples("where is order 12?")` returns the
   order-status example.
4. [ ] Write `agent.py` with the logging callback.
   Verify: in `adk run`, each intent logs a different example set and the reply
   follows the taught format.
5. [ ] Run the same queries without `ExampleTool` and capture the output for the README.
6. [ ] Write `cleanup.py`.
   Verify: the store no longer appears in `ExampleStore.list` or the console.
7. [ ] Write `README.md` using the output captured in steps 4 and 5.
8. [ ] Follow the README from start to finish in a clean virtual environment.

## README outline

1. What you'll build: one paragraph and the architecture diagram
2. Prerequisites: GCP project, `aiplatform.googleapis.com` enabled, Application Default Credentials, IAM role
3. Create the store: `python setup_store.py`
4. Run the agent with `adk web` or `adk run` and try the four queries
5. Read the logged `<EXAMPLES>` block for each query
6. Compare the same queries without `ExampleTool`
7. Gotchas
8. Clean up

## Gotchas to document

These come from reading the ADK source. None has been checked at runtime yet.

- The query is only the first text part of the user message.
- Results scoring below 0.5 are dropped, and `top_k` is fixed at 10. Neither is configurable.
- Retrieval runs on every model call, including the call after a tool response.
  Each of those calls repeats the search with the same user message.
- `get_examples` makes a synchronous network call inside the async flow.
- When retrieval returns different examples, the system instruction changes,
  so context caching misses for that turn. `docs/guides/examples/example/index.md`
  already covers this.
- `ExampleTool` declares no function, so the model never calls it.

## Open questions

1. Where should the sample live: `contributing/samples/tools/example_store/`,
   or a standalone folder for teaching?
2. Who is the audience: course students (more explanation, `adk web`
   screenshots) or developers (a short README)?
3. Should the sample also include a custom in-memory `BaseExampleProvider`?
   It adds a file, but readers could run the sample without creating an
   Example Store.
4. Which model? `convert_examples_to_text` formats tool calls differently when
   the model name doesn't contain `gemini-2`.
