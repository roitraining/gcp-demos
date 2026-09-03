"""Register the already-built container as an Agent Runtime instance (1.7).

Run deploy_byoc.sh instead of this directly; it builds and pushes the image
first, then calls this. Separated out because the container registration is a
Python SDK call (there is no gcloud CLI for Agent Runtime).

Env in:
    PROJECT_ID, LOCATION (region), IMAGE_URI, LOG_LEVEL, MODEL_LOCATION
Prints the reasoning engine resource name on success.
"""

from __future__ import annotations

import os

import vertexai

PROJECT_ID = os.environ["PROJECT_ID"]
LOCATION = os.environ.get("LOCATION", "us-central1")
IMAGE_URI = os.environ["IMAGE_URI"]
LOG_LEVEL = os.environ.get("LOG_LEVEL", "info")
MODEL_LOCATION = os.environ.get("MODEL_LOCATION", "global")

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

# The class methods the ADK reasoning-engine contract exposes. This is the
# standard AdkApp method set; the platform routes SDK/playground calls to them.
CLASS_METHODS = [
    {"api_mode": "", "name": "get_session"},
    {"api_mode": "", "name": "list_sessions"},
    {"api_mode": "", "name": "create_session"},
    {"api_mode": "", "name": "delete_session"},
    {"api_mode": "async", "name": "async_get_session"},
    {"api_mode": "async", "name": "async_list_sessions"},
    {"api_mode": "async", "name": "async_create_session"},
    {"api_mode": "async", "name": "async_delete_session"},
    {"api_mode": "stream", "name": "stream_query"},
    {"api_mode": "async_stream", "name": "async_stream_query"},
]

remote_agent = client.agent_engines.create(
    config={
        "display_name": "adk-logging-byoc",
        "description": "Tutorial 1.7: naive Part 1 logging in a custom container",
        "container_spec": {"image_uri": IMAGE_URI},
        "class_methods": CLASS_METHODS,
        "agent_framework": "google-adk",
        # Env the container reads. GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION
        # are RESERVED on Agent Runtime (the platform injects them) and rejected
        # if you set them here, so we pass only our own vars. Note: the platform
        # sets GOOGLE_CLOUD_LOCATION to the deploy region; the model lookup uses
        # it, which is why MODEL_LOCATION cannot be forced to "global" this way.
        "env_vars": {
            "LOG_LEVEL": LOG_LEVEL,
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            # Our own (non-reserved) var; main.py copies it over the reserved
            # GOOGLE_CLOUD_LOCATION so the model resolves in `global`, not the
            # deploy region.
            "MODEL_LOCATION": MODEL_LOCATION,
        },
    },
)

print(remote_agent.api_resource.name)
