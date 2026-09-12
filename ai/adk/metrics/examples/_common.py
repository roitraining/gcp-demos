"""Shared setup so each metrics example stays focused on the metric it teaches.

Every example starts with::

    from _common import bootstrap, ask, install_console_reader
    bootstrap()

``bootstrap()`` puts the folder root on ``sys.path`` (so ``demo_agent`` imports)
and loads ``.env``. ``ask()`` runs one turn against a Runner and returns the
final text. ``install_console_reader()`` installs a MeterProvider whose only
reader writes every histogram to a JSON file, which is what Part 1 opens.
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

    # ADK's JSON_SCHEMA_FOR_FUNC_DECL is on by default and warns once per run.
    # It is not a metrics concern, so keep it out of the tutorial's output.
    import warnings

    warnings.filterwarnings("ignore", message=r".*JSON_SCHEMA_FOR_FUNC_DECL.*")

    # genai's AFC advisory fires on ADK's own generate_content path; not ours.
    # It is a logging.warning (not a warnings.warn), so quiet that logger.
    import logging

    logging.getLogger("google_genai.models").setLevel(logging.ERROR)

    from dotenv import load_dotenv

    load_dotenv(_ROOT / ".env")
    if not os.getenv("GOOGLE_GENAI_USE_VERTEXAI") and not os.getenv("GOOGLE_API_KEY"):
        print(
            "WARNING: no model config found. Copy .env.example to .env first.",
            file=sys.stderr,
        )


def install_console_reader(out_path: str = "out/metrics.json") -> None:
    """Install a MeterProvider whose reader writes the histograms to a JSON file.

    This is ADK's own setup helper (``maybe_set_otel_providers``), the same one
    ``adk web`` uses, given a single reader instead of a cloud exporter. Nothing
    is recorded until a reader like this exists; with no provider installed the
    OTel API discards every ``record()`` call.

    The JSON goes to ``out_path`` (created if needed) rather than the console,
    because a full metrics dump is long and easier to read in an editor. The
    agent's own ``print`` output still goes to the console. The path is echoed to
    stderr so the reader knows what to open.

    The export interval is set very high so the reader does not fire mid-turn;
    the example drains it once with ``flush_metrics()`` at the end, so the file
    holds one clean block instead of a partial one plus a full one.
    """
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )

    from google.adk.telemetry.setup import OTelHooks, maybe_set_otel_providers

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = path.open("w")
    print(f"(metrics written to {out_path})", file=sys.stderr)

    reader = PeriodicExportingMetricReader(
        ConsoleMetricExporter(out=out),
        export_interval_millis=3_600_000,
    )
    maybe_set_otel_providers([OTelHooks(metric_readers=[reader])])


def install_inmemory_reader():
    """Install a MeterProvider whose reader keeps datapoints in the process.

    Same setup as ``install_console_reader`` but with an ``InMemoryMetricReader``
    instead of a console exporter, so the script can pull the recorded histograms
    back out (``reader.get_metrics_data()``) and draw them rather than print JSON.
    Returns the reader.
    """
    from opentelemetry.sdk.metrics.export import InMemoryMetricReader

    from google.adk.telemetry.setup import OTelHooks, maybe_set_otel_providers

    reader = InMemoryMetricReader()
    maybe_set_otel_providers([OTelHooks(metric_readers=[reader])])
    return reader


def find_datapoint(metrics_data, metric_name, attr=None):
    """Return the datapoint for ``metric_name`` matching ``attr``, or None.

    ``attr`` is an optional dict of attribute key/values the datapoint must
    carry, used to pick one series when the metric splits (e.g. input vs output
    tokens).
    """
    for rm in metrics_data.resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name != metric_name:
                    continue
                for point in metric.data.data_points:
                    if attr and not attr.items() <= dict(point.attributes).items():
                        continue
                    return point
    return None


def summarize_series(metrics_data, metric_name: str) -> str:
    """Summarize one metric as a line per series: its attributes and count.

    The console reader prints every datapoint as full JSON, which buries the one
    thing 1.3 teaches (a metric splitting into series) under bucket arrays and
    timestamps. This reads the same recorded datapoints and prints, for each
    series, only the attributes that identify it and its count.
    """
    lines = [metric_name]
    for rm in metrics_data.resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name != metric_name:
                    continue
                for point in metric.data.data_points:
                    attrs = ", ".join(f"{k}={v}" for k, v in point.attributes.items())
                    lines.append(f"  {{{attrs}}}  count={point.count}")
    return "\n".join(lines)


def render_histogram(point, *, width: int = 40) -> str:
    """Draw a histogram datapoint as labeled terminal bars.

    Reads ``bucket_counts`` and ``explicit_bounds`` straight off the datapoint,
    skips leading and trailing empty buckets, and scales the tallest bar to
    ``width`` blocks. This is the same data the console reader prints as JSON.
    """
    counts = list(point.bucket_counts)
    bounds = list(point.explicit_bounds)
    labels = ["≤ %g" % bounds[0]]
    labels += ["%g–%g" % (bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]
    labels.append("> %g" % bounds[-1])

    first = next((i for i, c in enumerate(counts) if c), 0)
    last = next((i for i in range(len(counts) - 1, -1, -1) if counts[i]), len(counts) - 1)
    peak = max(counts) or 1
    label_w = max(len(labels[i]) for i in range(first, last + 1))

    lines = []
    for i in range(first, last + 1):
        bar = "█" * round(counts[i] / peak * width)
        lines.append(f"{labels[i]:>{label_w}} | {bar} {counts[i]}")
    return "\n".join(lines)


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
