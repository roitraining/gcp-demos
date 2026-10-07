"""Upserts the examples in examples.py into the store named in .env."""

import os

import _common  # noqa: F401  (loads .env and initializes Vertex AI)
from examples import EXAMPLES
from vertexai.preview import example_stores

# The service accepts at most 5 examples per upsert call.
BATCH_SIZE = 5

store = example_stores.ExampleStore(os.environ["EXAMPLE_STORE_NAME"])

for start in range(0, len(EXAMPLES), BATCH_SIZE):
  batch = EXAMPLES[start:start + BATCH_SIZE]
  response = store.upsert_examples(batch, overwrite=True)
  for result in response["results"]:
    example = result["example"]["stored_contents_example"]
    print(f"stored: {example['search_key']}")
