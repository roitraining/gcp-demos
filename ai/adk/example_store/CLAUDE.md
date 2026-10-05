# ADK Example Store tutorial

## Governing model

The agent never calls the store. `ExampleTool` searches it with the user's
message before every model call and pastes the matches into the system
instruction as an `<EXAMPLES>` block. Every page shows one part of that path.

## Facts that are easy to get wrong (google-adk 2.11.0, aiplatform 2.3.0)

- `ExampleStore.create` takes about 8 to 9 minutes (486 s, 542 s). Setup starts it so Part 1 runs
  while it builds.
- `create` crashes on a dict `example_store_config`; pass
  `ExampleStoreConfig(...)`.
- `VertexAiExampleStore` asks for `top_k=10` and drops scores below 0.5. Neither
  is configurable.
- One upsert call takes at most 5 examples; `load_examples.py` batches.
- On 2026-10-05, about 1 search in 6 returned a 500. ADK doesn't retry, so the
  turn fails. Captures retry the command, not the code.
- The query is the first text part of the turn's user message
  (`tool_context.user_content`), so the search repeats unchanged on the model
  call after a tool response.

## Conventions

- Captures use `jwd-dev-5`, store in `us-central1`, Gemini on `global`. Save
  run output under `verification/`.
- The four questions are "Where is order 4417?", "Where's my order?",
  "I want a refund for order 5521.", and "What's a good recipe for pancakes?".
  None of them is a stored example's search key.
- `agents/no_examples` and `agents/with_examples` differ only by `ExampleTool`;
  shared code lives in `agents/orders.py`.
