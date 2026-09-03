"""Example 02: tame the server (uvicorn) access logs.

Use case
--------
ADK serves over uvicorn. Two things surprise people:

1. ``adk web --log_level ERROR`` still prints uvicorn access logs, because the
   CLI starts uvicorn without a ``log_config``, so uvicorn's own default logging
   config governs the ``uvicorn.access`` logger independently of ``--log_level``.
2. A load balancer or Cloud Run health check hits your service constantly, and
   every hit is one access log line. In production that is mostly noise.

When you run your own server (example 06), you fix both by passing a
``log_config`` to uvicorn. This example shows a config that:

* routes ``uvicorn.access`` through the same handler as everything else, and
* drops access-log lines for health-check style paths.

Run it
------
    .venv/bin/python examples/02_tame_uvicorn.py
    # in another terminal, compare the two:
    curl -s localhost:8081/healthz         # produces NO access log line
    curl -s localhost:8081/                 # produces one access log line
"""

from __future__ import annotations

import logging
import os

from _common import bootstrap

bootstrap()

from fastapi import FastAPI


class DropHealthChecks(logging.Filter):
    """Drop uvicorn access-log records for noisy health-check paths."""

    NOISY_PATHS = ("/healthz", "/health", "/readyz", "/livez")

    def filter(self, record: logging.LogRecord) -> bool:
        # uvicorn.access formats args as: (client, method, path, http_version, status)
        if record.args and len(record.args) >= 3:
            path = str(record.args[2])
            if any(path.startswith(p) for p in self.NOISY_PATHS):
                return False  # drop it
        return True


# A uvicorn log_config. Passing this to uvicorn.run(log_config=...) REPLACES
# uvicorn's default config, so we control uvicorn.error and uvicorn.access.
UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"drop_health": {"()": DropHealthChecks}},
    "formatters": {
        "default": {"format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s"},
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s - ACCESS - %(client_addr)s "%(request_line)s" %(status_code)s',
        },
    },
    "handlers": {
        "default": {"class": "logging.StreamHandler", "formatter": "default"},
        "access": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "filters": ["drop_health"],
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}

app = FastAPI(title="Uvicorn access-log demo")


@app.get("/")
async def root():
    return {"ok": True, "hint": "this request WAS logged"}


@app.get("/healthz")
async def healthz():
    return {"status": "healthy", "hint": "this request was NOT logged"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8081"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_config=UVICORN_LOG_CONFIG)
