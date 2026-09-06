"""Shared setup so each metrics example stays focused on the metric it teaches.

Every example starts with::

    from _common import bootstrap, ask, install_console_reader
    bootstrap()

``bootstrap()`` puts the folder root on ``sys.path`` (so ``demo_agent`` imports)
and loads ``.env``. ``ask()`` runs one turn against a Runner and returns the
final text. ``install_console_reader()`` installs a MeterProvider whose only
reader prints every histogram to the console, which is what Part 1 reads.
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


def install_console_reader(interval_ms: int = 1000) -> None:
    """Install a MeterProvider whose reader prints histograms to the console.

    This is ADK's own setup helper (``maybe_set_otel_providers``), the same one
    ``adk web`` uses, given a single console reader instead of a cloud exporter.
    Nothing prints until a reader like this exists; with no provider installed
    the OTel API discards every ``record()`` call.
    """
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )

    from google.adk.telemetry.setup import OTelHooks, maybe_set_otel_providers

    reader = PeriodicExportingMetricReader(
        ConsoleMetricExporter(),
        export_interval_millis=interval_ms,
    )
    maybe_set_otel_providers([OTelHooks(metric_readers=[reader])])


def flush_metrics() -> bool:
    """Drain the metric reader before the script exits.

    ADK installs the MeterProvider with ``shutdown_on_exit=False`` so points are
    not collected too close together, so a script that exits within the export
    interval of its last turn exports nothing unless it flushes first.
    """
    from opentelemetry import metrics

    return metrics.get_meter_provider().force_flush()


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
