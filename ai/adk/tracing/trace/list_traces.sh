#!/usr/bin/env bash
# List recent traces from the Cloud Trace v1 API, newest first, one id per line.
#
# Usage:   trace/list_traces.sh FILTER [MINUTES] [PROJECT_ID]
#   FILTER    a v1 list filter, e.g. 'span:"execute_tool get_forecast"' or
#             'root:invocation'. Quote a value that contains a space, or each
#             word becomes its own term and nothing matches. Pass a filter: an
#             unfiltered list can return an empty first page.
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

START="$(python3 -c "import datetime,sys; print((datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(minutes=int(sys.argv[1]))).strftime('%Y-%m-%dT%H:%M:%SZ'))" "$MINUTES")"
TOKEN="$(gcloud auth application-default print-access-token)"

URL="https://cloudtrace.googleapis.com/v1/projects/${PROJECT}/traces?view=COMPLETE&startTime=${START}&pageSize=100"
[ -n "$FILTER" ] && URL="${URL}&filter=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$FILTER")"

# Retry when the per-minute read quota is exhausted (HTTP 429). ~1 minute at 10 s.
for attempt in $(seq 1 6); do
  RESP="$(curl -s -H "Authorization: Bearer ${TOKEN}" "$URL")"
  if ! grep -q 'RESOURCE_EXHAUSTED' <<<"$RESP" || [ "$attempt" -eq 6 ]; then
    break
  fi
  echo "read quota exhausted (attempt ${attempt}/6), retrying in 10s..." >&2
  sleep 10
done

# The response goes in on stdin, so the script is passed with -c, not a heredoc.
printf '%s' "$RESP" | python3 -c '
import json, sys
d = json.load(sys.stdin)
if "error" in d:
    print(json.dumps(d["error"]), file=sys.stderr); sys.exit(1)
traces = d.get("traces", [])
# Sort by the newest span start time in each trace, descending.
def newest(t):
    return max((s.get("startTime","") for s in t.get("spans",[])), default="")
for t in sorted(traces, key=newest, reverse=True):
    print(t["traceId"] + "  " + str(len(t.get("spans", []))) + " spans")
print("(" + str(len(traces)) + " traces)", file=sys.stderr)
'
