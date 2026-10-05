[← 3.2 · When retrieval runs](part-3/3.2-when-retrieval-runs.md)<br>
[Tutorial index](../TUTORIAL.md)

---

# Reference

Everything this tutorial found, in one place. Each row links to the page that
shows it.

## Gotchas

| Gotcha | Consequence | Where |
|---|---|---|
| Creating a store takes about 8 to 9 minutes. | Start it before anything else. | [Setup](00-setup.md) |
| `ExampleStore.create` crashes on a dict `example_store_config` in `google-cloud-aiplatform` 2.3.0. | Pass `ExampleStoreConfig(vertex_embedding_model=...)`, as [store/create_store.py](../store/create_store.py) does. | [Setup](00-setup.md) |
| One upsert call takes at most 5 examples. | Load in batches. | [2.1](part-2/2.1-load-the-examples.md) |
| ADK keeps up to 10 matches scoring 0.5 or more; neither number is configurable. | In one domain, most examples clear the cutoff. | [2.2](part-2/2.2-search-the-store.md) |
| About one search in six returned a 500, and ADK does not retry. | The turn fails with `Error: 500`; rerun it. | [2.2](part-2/2.2-search-the-store.md#why-do-some-searches-fail) |
| The model never calls `ExampleTool`. | It only edits the request. | [3.1](part-3/3.1-add-exampletool.md#does-the-model-call-exampletool) |
| Example tool calls use `tool_code` fences unless the model name contains `gemini-2`. | The format differs between model families. | [3.1](part-3/3.1-add-exampletool.md#what-does-gemini-receive) |
| Every model call searches again, with the same text. | A tool-using turn searches twice. | [3.2](part-3/3.2-when-retrieval-runs.md) |
| The search uses the first text part of the turn's user message, nothing else. | Short follow-ups make weak queries. | [3.2](part-3/3.2-when-retrieval-runs.md) |
| The search blocks ADK's async flow. | About 1 to 3 seconds per search in these runs. | [3.2](part-3/3.2-when-retrieval-runs.md#does-the-search-slow-the-turn-down) |
| Different examples mean a different system instruction. | Context caching misses. | [3.2](part-3/3.2-when-retrieval-runs.md#do-examples-affect-context-caching) |

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Embedding model | `text-embedding-005` | A current Vertex AI text embedding model |
| Store region | `us-central1` | Gemini stays on `global` in `.env` |
| Search key | The example's user message | ADK searches with the user's message |
| Comparison | Two agent folders | Same questions, no code edits between runs |
| Visibility | A `before_model_callback` that logs example lines | Retrieval is otherwise invisible |

## Verification status

Ran on 2026-10-05 against project `jwd-dev-5`, google-adk 2.11.0,
google-cloud-aiplatform 2.3.0, Python 3.13, Gemini 3.7 Flash. Run records
are in [verification/](../verification/).

| What | Result |
|---|---|
| Store create | 486 s and 542 s on two runs |
| Upsert of 8 examples | Rejected in one call; loaded in two batches |
| Searches for the four questions | Captured on 2.2 |
| Agent without and with examples | Captured on Part 1 and 3.1; all four replies matched the stored ones |
| Two searches for a tool-using turn | Counted with a wrapper around `get_examples` |
| Search errors | 5 of 30 searches returned 500; 2 of 12 `adk run` turns failed |
| Store delete | Ran; `ExampleStore.list()` then returned no stores |

**Not verified**

| What | Why |
|---|---|
| The IAM role a non-owner needs | Runs used an owner account |
| Cost of an idle store | Not checked |
| `adk web` screenshots | Not captured; every page uses `adk run` |
| Whether the 500 rate is persistent | Seen on one day, in one project |

## Links

- [Example Store overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/optimize/example-store/overview)
- [Example Store with Gemini quickstart](https://docs.cloud.google.com/gemini-enterprise-agent-platform/optimize/example-store/quickstart)
- [ADK `ExampleTool` source](https://github.com/google/adk-python/blob/main/src/google/adk/tools/example_tool.py)

---

[← 3.2 · When retrieval runs](part-3/3.2-when-retrieval-runs.md)<br>
[Tutorial index](../TUTORIAL.md)
