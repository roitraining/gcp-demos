#!/usr/bin/env bash
# List recent traces from the Cloud Trace v1 API, newest first, one id per line.
#
# Usage:   trace/list_traces.sh [FILTER] [MINUTES] [PROJECT_ID]
#   FILTER    a v1 list filter, e.g. 'span:execute_tool get_forecast' or
#             'root:invocation'. Empty for all.
#   MINUTES   look-back window (default 30).
#   PROJECT_ID defaults to $PROJECT_ID, then the gcloud default project.
#
# Prints "<traceId>  <span count>" per trace. Pipe a trace id into get_trace.sh
# to see its tree. The v1 API's ~90-120 s ingestion delay applies here too.
set -euo pipefail

FILTER="${1:-}"
MINUTES="${2:-30}"
PROJECT="${3:-${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}}"
[ -n "$PROJECT" ] || { echo "no project: pass one or set PROJECT_ID" >&2; exit 2; }

START="$(python3 -c "import datetime,sys; print((datetime.datetime.utcnow()-datetime.timedelta(minutes=int(sys.argv[1]))).strftime('%Y-%m-%dT%H:%M:%SZ'))" "$MINUTES")"
TOKEN="$(gcloud auth application-default print-access-token)"

URL="https://cloudtrace.googleapis.com/v1/projects/${PROJECT}/traces?view=COMPLETE&startTime=${START}&pageSize=100"
[ -n "$FILTER" ] && URL="${URL}&filter=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$FILTER")"

curl -s -H "Authorization: Bearer ${TOKEN}" "$URL" | python3 - <<'PY'
import json, sys
d = json.load(sys.stdin)
if "error" in d:
    print(json.dumps(d["error"]), file=sys.stderr); sys.exit(1)
traces = d.get("traces", [])
# Sort by the newest span start time in each trace, descending.
def newest(t):
    return max((s.get("startTime","") for s in t.get("spans",[])), default="")
for t in sorted(traces, key=newest, reverse=True):
    print(f"{t['traceId']}  {len(t.get('spans',[]))} spans")
print(f"({len(traces)} traces)", file=sys.stderr)
PY
