# ADK few-shot examples with Vertex AI Example Store

A hands-on tour of teaching an ADK agent by example. You store sample
conversations in a Vertex AI Example Store, attach the store to an agent
with `ExampleTool`, and compare the agent's replies with and without it.

The one idea that makes the rest simple: **the agent never calls the store.**
Before each model call, `ExampleTool` searches the store with the user's
message and adds the matches to the system instruction.

Start with **[TUTORIAL.md](TUTORIAL.md)**.

> Verified against google-adk 2.11.0 and google-cloud-aiplatform 2.3.0 on
> Python 3.13, serving Gemini 3.7 Flash via Vertex AI.

## Files

| Path | What it is | Used on |
|---|---|---|
| [TUTORIAL.md](TUTORIAL.md) | The tutorial index: intro, diagram, and contents. Start here. | |
| [tutorial/](tutorial/) | Setup, three parts, and a reference page. | |
| [agents/orders.py](agents/orders.py) | The shared order tool, instruction, model, and the callback that logs examples. | every page |
| [agents/no_examples/](agents/no_examples/) | The agent with no examples. | Part 1 |
| [agents/with_examples/](agents/with_examples/) | The same agent plus `ExampleTool`. | Part 3 |
| [store/create_store.py](store/create_store.py) | Creates the empty store. | Setup |
| [store/examples.py](store/examples.py) | The eight examples, two per intent. | 2.1 |
| [store/load_examples.py](store/load_examples.py) | Upserts the examples. | 2.1 |
| [store/search.py](store/search.py) | Searches the way ADK does and prints scores. | 2.2, 3.2 |
| [store/delete_store.py](store/delete_store.py) | Deletes the store. | 3.2 |
| [verification/](verification/) | Captured run output. | |

## Quick start

Follow [Setup](tutorial/00-setup.md).

## Status

Complete and verified end to end on 2026-10-05. See
[Reference](tutorial/reference.md#verification-status) for what ran and what
is not verified.
