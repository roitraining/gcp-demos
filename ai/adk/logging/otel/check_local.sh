#!/usr/bin/env bash
#
# Part 5.1 check: with nothing configured, the ADK CLI server still traces every
# turn into process memory. Starts a plain `adk web` (its /dev debug endpoint is
# the only way to read those spans back; `adk api_server` installs the same
# in-memory exporters but registers no /dev routes), runs one turn over HTTP,
# and asserts the expected span names. Needs the model (Vertex AI via ADC) but
# no telemetry flags, no env vars, and no cloud export.
#
# Usage (from ai/adk/logging):
#   ./otel/check_local.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PORT="${PORT:-8000}"
SID="check-$(date +%s)"
LOG="${TMPDIR:-/tmp}/check_local.log"

.venv/bin/adk web --port "$PORT" ./ > "$LOG" 2>&1 &
PID=$!
trap 'kill -INT "$PID" 2>/dev/null; wait "$PID" 2>/dev/null || true' EXIT
for _ in $(seq 1 60); do
  [[ "$(curl -s -o /dev/null -w '%{http_code}' "localhost:$PORT/list-apps")" == "200" ]] && break
  sleep 1
done

curl -s -X POST "localhost:$PORT/apps/demo_agent/users/u1/sessions/$SID" \
     -H 'content-type: application/json' -d '{}' > /dev/null
curl -s -X POST "localhost:$PORT/run" \
     -H 'content-type: application/json' \
     -d '{"app_name":"demo_agent","user_id":"u1","session_id":"'"$SID"'",
          "new_message":{"role":"user","parts":[{"text":"What'\''s the weather in London?"}]}}' > /dev/null

NAMES="$(curl -s "localhost:$PORT/dev/apps/demo_agent/debug/trace/session/$SID" \
  | python3 -c 'import json, sys; print("\n".join(s["name"] for s in json.load(sys.stdin)))')"

status=0
for expected in "invocation:1" "invoke_agent weather_agent:1" "call_llm:2" \
                "generate_content gemini-3.7-flash:2" "execute_tool get_weather:1"; do
  name="${expected%:*}"; want="${expected##*:}"
  got="$(printf '%s\n' "$NAMES" | grep -cx "$name" || true)"
  if [[ "$got" -eq "$want" ]]; then
    echo "ok       $name x$got"
  else
    echo "MISMATCH $name (want $want, got $got)"; status=1
  fi
done
exit $status
