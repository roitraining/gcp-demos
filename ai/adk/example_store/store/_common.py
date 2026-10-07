"""Loads .env and points the Vertex AI SDK at the store's project and region."""

import os

from dotenv import load_dotenv
import vertexai

# The store lives in us-central1; Gemini in .env can stay on `global`.
STORE_LOCATION = "us-central1"

load_dotenv()
vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"], location=STORE_LOCATION)
