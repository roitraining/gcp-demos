#!/usr/bin/env bash
# Print one trace as an indented span tree, read from the Cloud Trace v1 API.
#
# Usage:   trace/get_trace.sh <TRACE_ID> [PROJECT_ID]
#   TRACE_ID    32 hex chars (what a server returns, or the root span's trace id).
#   PROJECT_ID  defaults to $PROJECT_ID, then the gcloud default project.
#
# The v1 API reads spans ingested through telemetry.googleapis.com. Two quirks it
# handles for you: spanId comes back as a decimal uint64 (not hex), and a freshly
# exported trace 404s for ~90-120 s with "Trace bucket not found" while it
# indexes, so this retries before giving up.
set -euo pipefail

TRACE_ID="${1:?usage: get_trace.sh <TRACE_ID> [PROJECT_ID]}"
PROJECT="${2:-${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}}"
[ -n "$PROJECT" ] || { echo "no project: pass one or set PROJECT_ID" >&2; exit 2; }

URL="https://cloudtrace.googleapis.com/v1/projects/${PROJECT}/traces/${TRACE_ID}"
TOKEN="$(gcloud auth application-default print-access-token)"

# Retry on the indexing 404. ~2 minutes at 10 s.
for attempt in $(seq 1 12); do
  RESP="$(curl -s -H "Authorization: Bearer ${TOKEN}" "$URL")"
  if ! grep -q '"error"' <<<"$RESP"; then
    break
  fi
  if [ "$attempt" -lt 12 ]; then
    echo "trace not indexed yet (attempt ${attempt}/12), retrying in 10s..." >&2
    sleep 10
  else
    echo "$RESP" >&2
    echo "gave up after ~2 min; the trace may still be indexing" >&2
    exit 1
  fi
done

# Render the flat span list as an indented tree, keyed on the decimal spanId.
python3 - "$RESP" <<'PY'
import json, sys
trace = json.loads(sys.argv[1])
spans = trace.get("spans", [])
kids = {}
for s in spans:
    kids.setdefault(s.get("parentSpanId"), []).append(s)
def dur(s):
    from datetime import datetime
    f = "%Y-%m-%dT%H:%M:%S.%fZ"
    try:
        a = datetime.strptime(s["startTime"], f); b = datetime.strptime(s["endTime"], f)
        return f"{(b-a).total_seconds():.3f}s"
    except Exception:
        return ""
def walk(parent, depth):
    for s in sorted(kids.get(parent, []), key=lambda s: s.get("startTime", "")):
        print(f"{'  '*depth}{s['name']:40s} {dur(s)}")
        walk(s["spanId"], depth+1)
roots = [s for s in spans if s.get("parentSpanId") not in {x["spanId"] for x in spans}]
print(f"trace {trace.get('traceId')}  ({len(spans)} spans)")
for r in sorted(roots, key=lambda s: s.get("startTime", "")):
    print(f"{r['name']:40s} {dur(r)}")
    walk(r["spanId"], 1)
PY
