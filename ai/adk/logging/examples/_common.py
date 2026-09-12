"""Shared setup for the examples so each file can stay focused on logging.

Every example starts with::

    from _common import bootstrap, ask
    bootstrap()

``bootstrap()`` puts the folder root on ``sys.path`` (so ``demo_agent`` imports)
and loads ``.env``. ``ask()`` runs one turn against a Runner and returns the
final text, so the examples do not each re-implement the run loop.
``JsonFormatter`` is the minimal JSON line formatter examples 05 and 06 both
build on, kept here so there's one place that defines "what counts as an
extra field" instead of two copies drifting apart.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent


class JsonFormatter(logging.Formatter):
    """Minimal JSON line formatter. Example 06 extends this for Cloud Run."""

    # Attributes present on every LogRecord; anything else was passed via extra.
    _RESERVED = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(self._build_payload(record), default=str)

    def _build_payload(self, record: logging.LogRecord) -> dict[str, Any]:
        payload = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        for key, value in record.__dict__.items():
            if key not in self._RESERVED:
                payload[key] = value
        return payload


def bootstrap() -> None:
    """Put the folder root on the path and load .env (idempotent)."""
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    from dotenv import load_dotenv

    load_dotenv(_ROOT / ".env")
    if not os.getenv("GOOGLE_GENAI_USE_VERTEXAI") and not os.getenv("GOOGLE_API_KEY"):
        print(
            "WARNING: no model config found. Copy .env.example to .env first.",
            file=sys.stderr,
        )


async def ask(runner, text: str, *, user_id: str = "u1") -> str:
    """Send one message through a Runner and return the final response text."""
    from google.genai import types

    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id=user_id
    )
    message = types.Content(role="user", parts=[types.Part(text=text)])
    final = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content:
            final = event.content.parts[0].text
    return final
