#!/usr/bin/env bash
#
# Fire N turns of one named scenario at a running ADK server.
#
# Every page from Part 2 on generates load with this one script, so the trace a
# page reads back traces to a scenario in tutorial/scenarios.md, not to an ad-hoc
# curl. Each scenario owns its prompts and its session behavior.
#
# Usage:
#   ./load/turns.sh <scenario> [N]
#
# Scenarios (see tutorial/scenarios.md):
#   baseline         One London turn per fresh session.
#   slow-tool        Half the turns ask for a 3-day forecast (get_forecast sleeps).
#   returned-error   Half ask for Atlantis (an error status, no raise).
#   multi-turn       All N turns reuse ONE session (a whole conversation).
#   concurrent       slow-tool and baseline turns fired in parallel, each its own
#                    session, to check logs stay attached to the right request.
#
# Prints one line per turn: scenario, index, HTTP status, elapsed, and the trace
# id if the server returned one (the 02-04 custom servers put it in the /chat
# response; adk web's /run does not, so that field is blank there).
#
# Env:
#   HOST      server base URL         (default http://localhost:8000)
#   APP_NAME  agent folder / app name (default demo_agent, for the /run path)
#   USER_ID   user id for sessions    (default load-user)
#   ENDPOINT  "run" (adk web /run) or "chat" (custom servers) (default run)
set -euo pipefail

SCENARIO="${1:?usage: turns.sh <scenario> [N]}"
N="${2:-10}"

HOST="${HOST:-http://localhost:8000}"
APP_NAME="${APP_NAME:-demo_agent}"
USER_ID="${USER_ID:-load-user}"
ENDPOINT="${ENDPOINT:-run}"

Q_LONDON="What's the weather in London?"
Q_ATLANTIS="What's the weather in Atlantis?"
Q_FORECAST="What's the three-day forecast for London?"

# --- one turn against a custom /chat server -------------------------------
# The 02-04 servers take {"text": "..."} and return {"trace_id": "...", ...}.
chat_turn() {
  local idx="$1" prompt="$2"
  local esc="${prompt//\"/\\\"}"
  local start end elapsed resp tid
  start=$(date +%s.%N)
  resp=$(curl -s -X POST "${HOST}/chat" -H 'content-type: application/json' \
    -d "$(printf '{"text":"%s"}' "$esc")")
  end=$(date +%s.%N)
  elapsed=$(awk "BEGIN{printf \"%.2f\", ${end}-${start}}")
  tid=$(sed -n 's/.*"trace_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' <<<"$resp" | head -1)
  printf '%-15s turn %3d  %ss  trace=%s\n' "$SCENARIO" "$idx" "$elapsed" "${tid:-—}"
}

# --- one turn against adk web /run ----------------------------------------
run_turn() {
  local idx="$1" prompt="$2" session_id="${3:-}"
  if [[ -z "$session_id" ]]; then
    session_id=$(curl -s -X POST \
      "${HOST}/apps/${APP_NAME}/users/${USER_ID}/sessions" \
      -H 'content-type: application/json' -d '{}' \
      | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
  fi
  local esc="${prompt//\"/\\\"}"
  local body start end elapsed code
  body=$(printf '{"app_name":"%s","user_id":"%s","session_id":"%s","new_message":{"role":"user","parts":[{"text":"%s"}]}}' \
    "$APP_NAME" "$USER_ID" "$session_id" "$esc")
  start=$(date +%s.%N)
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${HOST}/run" \
    -H 'content-type: application/json' -d "$body")
  end=$(date +%s.%N)
  elapsed=$(awk "BEGIN{printf \"%.2f\", ${end}-${start}}")
  printf '%-15s turn %3d  http=%s  %ss  session=%s\n' "$SCENARIO" "$idx" "$code" "$elapsed" "$session_id"
}

# Dispatch one turn to the configured endpoint.
turn() {
  if [[ "$ENDPOINT" == "chat" ]]; then chat_turn "$1" "$2"; else run_turn "$1" "$2" "${3:-}"; fi
}

case "$SCENARIO" in
  baseline)
    for i in $(seq 1 "$N"); do turn "$i" "$Q_LONDON"; done
    ;;
  slow-tool)
    for i in $(seq 1 "$N"); do
      if (( i % 2 == 0 )); then turn "$i" "$Q_FORECAST"; else turn "$i" "$Q_LONDON"; fi
    done
    ;;
  returned-error)
    for i in $(seq 1 "$N"); do
      if (( i % 2 == 0 )); then turn "$i" "$Q_ATLANTIS"; else turn "$i" "$Q_LONDON"; fi
    done
    ;;
  multi-turn)
    # One shared session across all N turns (the /run path only; /chat is stateless here).
    session_id=$(curl -s -X POST \
      "${HOST}/apps/${APP_NAME}/users/${USER_ID}/sessions" \
      -H 'content-type: application/json' -d '{}' \
      | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
    for i in $(seq 1 "$N"); do run_turn "$i" "$Q_LONDON" "$session_id"; done
    ;;
  concurrent)
    for i in $(seq 1 "$N"); do
      if (( i % 2 == 0 )); then turn "$i" "$Q_FORECAST" & else turn "$i" "$Q_LONDON" & fi
    done
    wait
    ;;
  *)
    echo "unknown scenario: ${SCENARIO}" >&2
    echo "one of: baseline slow-tool returned-error multi-turn concurrent" >&2
    exit 2
    ;;
esac
