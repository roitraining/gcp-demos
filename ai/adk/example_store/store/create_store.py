"""Creates an empty Example Store and prints the line to add to .env."""

import _common  # noqa: F401  (loads .env and initializes Vertex AI)
from vertexai.preview import example_stores

store = example_stores.ExampleStore.create(
    display_name="order-support-examples",
    example_store_config=example_stores.ExampleStoreConfig(
        vertex_embedding_model="text-embedding-005"
    ),
)
print(f"\nEXAMPLE_STORE_NAME={store.resource_name}")
