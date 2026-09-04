"""Example 08: OpenTelemetry GenAI telemetry exported to Cloud Logging.

Use case
--------
Everything so far routed plain ``logging`` records. ADK ALSO emits OpenTelemetry
signals following the GenAI semantic conventions (spans for each LLM call and
tool call, plus structured GenAI events). This example wires those OTel signals
to an exporter so they leave the process, and shows the one knob that controls
whether prompt/response content travels with them.

This is the programmatic form of the ``adk web --otel_to_cloud`` flag. Under the
hood both call the same helpers used here.

Two modes
---------
* ``console`` (default): install a console span exporter so you can watch the
  OTel spans locally with no cloud access. Good for understanding what ADK emits.
* ``cloud``: install the Google Cloud exporters
  (``get_gcp_exporters(enable_cloud_tracing=True, enable_cloud_logging=True)``)
  so spans go to Cloud Trace and GenAI events go to Cloud Logging (under
  per-event ``gen_ai.*`` log names, e.g. ``gen_ai.user.message``). Requires
  ``GOOGLE_CLOUD_PROJECT`` and these extra packages::

      pip install opentelemetry-exporter-gcp-logging \\
                  opentelemetry-exporter-otlp-proto-http

Content capture (the privacy knob)
----------------------------------
``OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`` controls whether prompt
and response text rides along:

* ``NO_CONTENT`` (or unset): metadata only. The safe production default.
* ``SPAN_ONLY`` / ``EVENT_ONLY`` / ``SPAN_AND_EVENT``: include content.

Set it BEFORE importing ADK. This example defaults it to ``NO_CONTENT``.

Run it
------
    .venv/bin/python examples/08_otel_cloud.py            # console mode
    .venv/bin/python examples/08_otel_cloud.py cloud      # export to GCP
"""

from __future__ import annotations

import asyncio
import os
import sys

from _common import ask, bootstrap

bootstrap()

# Content-capture mode must be set before ADK reads it. Keep the safe default.
os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "NO_CONTENT")

from google.adk.runners import InMemoryRunner
from google.adk.telemetry.setup import OTelHooks, maybe_set_otel_providers

from demo_agent.agent import root_agent


def install_console_exporter() -> None:
    """Send OTel spans to the terminal. No cloud access needed."""
    from opentelemetry.sdk.trace.export import (
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )

    hooks = OTelHooks(
        span_processors=[SimpleSpanProcessor(ConsoleSpanExporter())],
        metric_readers=[],
        log_record_processors=[],
    )
    # maybe_set_otel_providers expects a LIST of hooks.
    maybe_set_otel_providers([hooks])


def install_cloud_exporters() -> None:
    """Send spans to Cloud Trace and GenAI events to Cloud Logging."""
    from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        sys.exit("cloud mode needs GOOGLE_CLOUD_PROJECT set (in .env)")

    hooks = get_gcp_exporters(
        enable_cloud_tracing=True,
        enable_cloud_logging=True,
    )
    # The telemetry.googleapis.com OTLP endpoint routes spans by the
    # gcp.project_id attribute on the OTel resource. Without it the export is
    # rejected with a 400. get_gcp_resource(project) supplies it.
    maybe_set_otel_providers([hooks], otel_resource=get_gcp_resource(project))
    print(f"Exporting OTel telemetry to project {project!r}.")
    print("  Traces:  Cloud Console > Trace > Trace explorer")
    print("  Logs:    Cloud Console > Logging  (log names 'gen_ai.*')")


async def main(mode: str) -> None:
    if mode == "cloud":
        install_cloud_exporters()
    else:
        install_console_exporter()

    capture = os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"]
    print(f"Content capture mode: {capture}\n")

    runner = InMemoryRunner(agent=root_agent, app_name="otel_demo")
    answer = await ask(runner, "What's the weather in London?")
    print("\nFINAL ANSWER:", answer)

    await runner.close()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "console"
    asyncio.run(main(mode))
