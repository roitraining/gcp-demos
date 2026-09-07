"""Draw the token-usage series as a two-line chart (tutorial 2.1, Door 2).

Reads the PromQL range-query JSON the page saved to ``out/metrics.json`` and
writes ``out/tokens.png``: one line per ``gen_ai.token.type`` over time. This is
the exact query Door 1 runs in the Console, so the chart you get here is the same
two lines the Console drew — same data, different tool.

Run it after the Door 2 curl has written out/metrics.json::

    .venv/bin/python examples/plot_tokens.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # write a file, no display needed
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402

SRC = Path("out/metrics.json")
DST = Path("out/tokens.png")


def read_series(path: Path) -> dict[str, tuple[list[datetime], list[float]]]:
    """Pull {token_type: (times, values)} out of the range-query response."""
    payload = json.loads(path.read_text())
    series: dict[str, tuple[list[datetime], list[float]]] = {}
    for entry in payload["data"]["result"]:
        token_type = entry["metric"]["gen_ai.token.type"]
        times = [datetime.fromtimestamp(float(ts), timezone.utc) for ts, _ in entry["values"]]
        values = [float(v) for _, v in entry["values"]]
        series[token_type] = (times, values)
    return series


def main() -> None:
    series = read_series(SRC)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for token_type, (times, values) in series.items():
        ax.plot(times, values, marker=".", label=token_type)

    ax.set_title("gen_ai.client.token.usage — tokens/min by type")
    ax.set_xlabel("time (UTC)")
    ax.set_ylabel("tokens per minute")
    ax.legend(title="gen_ai.token.type")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(DST, dpi=120)

    print(f"wrote {DST} — the same two lines Door 1 drew in the Console")


if __name__ == "__main__":
    main()
