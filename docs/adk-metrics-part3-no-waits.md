# ADK metrics: remove the 5-minute waits

Branch `adk-metrics-review-fixes`. Status: **approved 2026-10-03, in progress**.

## Problem

Part 3 separates pages by time. Every query uses a `[5m]` window, so each page
tells the reader to wait 5 minutes for the previous page's load to age out. On
top of that, 3.6's alert needs the ratio held for 5 minutes, so its load runs
about 8 minutes. A full Part 3 run spends about 35 minutes waiting.

In the 2026-10-03 student test, 3.6's incident also never opened, even though
the condition was met for 10+ minutes on `jwd-dev-2`.

## Design

Separate pages by **label** instead of by time.

- Each Part 3 page starts its server with its own `OTEL_SERVICE_NAME`, for
  example `adk-metrics-3-2`. Managed Prometheus turns that into the `job` label.
- Every query on the page filters on that `job`, so earlier pages' data and
  other sessions' traffic on a shared project can't leak in.
- No page waits for anything except ingestion (about 1 minute after its load).

Restarting the server costs each page one Step: Ctrl+C, then
`OTEL_SERVICE_NAME=adk-metrics-3-N .venv/bin/adk web --otel_to_cloud ./`.

## Decision needed: window length

`rate(x[W])` only sees the last `W`. Pages read after the load ends, and
ingestion adds about 1 minute, so a short window has slid past most of the load
by read time.

| Option | Reads after load | 3.6 alert |
|---|---|---|
| A. `[1m]` everywhere | Readings fall toward 0 or come back empty unless the reader queries within seconds of the load ending. Needs a test to confirm. | Works |
| **B. `[10m]` for reads, `[1m]` for the alert** (recommended) | Stable: the window covers the whole load, and the job filter keeps it clean | Works |

Answer: **B.** Reads use `[10m]`; the alert uses `[1m]` with a 60 s hold.

## Changes

| # | File(s) | Change |
|---|---|---|
| 1 | `tutorial/part-3/3.1` to `3.7` | Step 1 on each page restarts the server with `OTEL_SERVICE_NAME=adk-metrics-3-N`. Delete every "wait 5 minutes after the last page's load" line. |
| 2 | `queries/*.promql` (5 files) | Add `job="$JOB"` placeholder guidance in each header; change windows per the decision above |
| 3 | Part 3 pages' inline queries | Add `job="adk-metrics-3-N"` to every selector; change windows |
| 4 | `queries/alert-policy.json` | `job="adk-metrics-3-6"`, `[1m]` rate, `duration: 60s`, `evaluationInterval: 30s`. Update the display name and documentation text. |
| 5 | `tutorial/part-3/3.6` | Load drops from 120 turns to about 40. Add one sentence: production policies should hold 5 minutes or more. Recapture the incident. |
| 6 | `queries/dashboard.json`, `3.5` | Filter on `job="adk-metrics-3-5"` and change windows. A dashboard can't take a per-page variable, so 3.5 owns it. |
| 7 | Part 2 pages 2.1, 2.3, 2.4, 2.5 | Already job-filtered; change windows per the decision above |
| 8 | `scenarios.md`, Part 3 index, `CLAUDE.md` | Record the per-page job convention; remove any mention of waiting between pages |
| 9 | Part 3 pages | Recapture output on `jwd-dev-5` (no Model Armor floor), all seven pages in parallel, each on its own port and job. Part 2 is not recaptured: only its windows changed, from `[5m]` to `[10m]`. |

## Verification

1. 3.6 alone on `jwd-dev-2`: the incident opens within about 4 minutes of the
   load starting. If it doesn't, find out why before changing other pages.
2. Run 3.1 to 3.7 back to back with no waits. Each page's readings match its
   scenario, with no data from the previous page.
3. Total Part 3 wall time: target under 20 minutes, from about 55.

**Results (2026-10-03, `jwd-dev-5`, all seven pages in parallel):**

| Page | Server start to last read | Result |
|---|---|---|
| 3.1 (with concurrent deep dive) | About 4 min | Pass; prose updated to new numbers |
| 3.2 | About 3.5 min | Pass |
| 3.3 | 3.5 min | Pass |
| 3.4 | About 2.5 min | Pass; prose updated to new numbers |
| 3.5 | About 3 min | Pass; "error ratio reads 0" corrected to "empty" |
| 3.6 | Incident 4m08s after policy creation, about 2 min after the load ended | Pass |
| 3.7 | Under 4 min | Pass |

Every page read data on its first query, about 1 minute after its load. Run
back to back, Part 3 now takes about 25 minutes; in parallel, about 5.

## Notes

- 3.1's concurrent deep dive gets its own job, `adk-metrics-3-1c`, so it needs no wait either.
