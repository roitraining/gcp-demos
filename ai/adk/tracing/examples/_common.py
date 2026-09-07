"""Shared setup so each tracing example stays focused on the span it teaches.

Every local example starts with::

    from _common import bootstrap, ask, install_console_spans
    bootstrap()

``bootstrap()`` puts the folder root on ``sys.path`` (so ``demo_agent`` imports)
and loads ``.env``. ``ask()`` runs one turn against a Runner and returns the
final text. ``install_console_spans()`` installs a TracerProvider whose only
processor writes every span ADK opened during the turn to a JSON file, which is
what Part 1 opens. Nothing is *recorded* without a provider: with none installed
``trace.get_current_span()`` is a no-op span and every span ADK opens is dropped.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


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


def install_console_spans(out_path: str = "out/spans.json") -> None:
    """Install a TracerProvider whose processor writes each span to a JSON file.

    This is ADK's own setup helper (``maybe_set_otel_providers``), the same one
    ``adk web`` uses, given a ``SimpleSpanProcessor(ConsoleSpanExporter)`` instead
    of a cloud exporter. ``SimpleSpanProcessor`` exports each span the moment it
    ends, so the file is complete once the turn is; the script still flushes on
    exit (``flush_spans()``) to drain the batch the OTLP examples use.

    The JSON goes to ``out_path`` (created if needed) rather than the console,
    because a full span dump is long and easier to read in an editor. The agent's
    own ``print`` output still goes to the console. The path is echoed to stderr
    so the reader knows what to open.
    """
    from opentelemetry.sdk.trace.export import (
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )

    from google.adk.telemetry.setup import OTelHooks, maybe_set_otel_providers

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = path.open("w")
    print(f"(spans written to {out_path})", file=sys.stderr)

    processor = SimpleSpanProcessor(ConsoleSpanExporter(out=out))
    maybe_set_otel_providers([OTelHooks(span_processors=[processor])])


def flush_spans() -> bool:
    """Drain the span processor before the script exits.

    A ``BatchSpanProcessor`` holds spans until its interval elapses, so a script
    that exits right after its turn loses the last batch unless it flushes first.
    ``SimpleSpanProcessor`` (used by ``install_console_spans``) exports on span
    end and does not need this, but the call is harmless and the OTLP examples do.
    """
    from opentelemetry import trace

    provider = trace.get_tracer_provider()
    flush = getattr(provider, "force_flush", None)
    return bool(flush()) if flush else False


async def ask(runner, text: str, *, user_id: str = "u1", session_id: str | None = None) -> str:
    """Send one message through a Runner and return the final response text.

    Pass ``session_id`` to keep several turns in one session (the multi-turn
    scenario, 1.5); omit it and a fresh session is created per call.
    """
    from google.genai import types

    if session_id is None:
        session = await runner.session_service.create_session(
            app_name=runner.app_name, user_id=user_id
        )
        session_id = session.id

    message = types.Content(role="user", parts=[types.Part(text=text)])
    final = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=message
    ):
        if event.is_final_response() and event.content:
            final = event.content.parts[0].text
    return final
