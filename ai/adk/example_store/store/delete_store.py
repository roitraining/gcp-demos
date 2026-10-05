"""Deletes the store named in .env, with the examples in it."""

import os

import _common  # noqa: F401  (loads .env and initializes Vertex AI)
from vertexai.preview import example_stores

example_stores.ExampleStore(os.environ["EXAMPLE_STORE_NAME"]).delete()
