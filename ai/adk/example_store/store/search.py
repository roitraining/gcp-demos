"""Searches the store the way ADK does and prints each match's score.

Usage: python store/search.py "where is order 4417?"
"""

import os
import sys

import _common  # noqa: F401  (loads .env and initializes Vertex AI)
from vertexai.preview import example_stores

# ADK's VertexAiExampleStore drops matches below this score.
ADK_MIN_SCORE = 0.5

store = example_stores.ExampleStore(os.environ["EXAMPLE_STORE_NAME"])
# The same request VertexAiExampleStore.get_examples sends.
response = store.search_examples(
    {
        "stored_contents_example_key": {
            "contents": [{"role": "user", "parts": [{"text": sys.argv[1]}]}],
            "search_key_generation_method": {"last_entry": {}},
        }
    },
    top_k=10,
)

for result in response.get("results", []):
  score = result["similarity_score"]
  key = result["example"]["stored_contents_example"]["search_key"]
  verdict = "kept" if score >= ADK_MIN_SCORE else "dropped"
  print(f"{score:.2f}  {verdict:7}  {key}")
