#!/usr/bin/env bash
#
# Fire N turns of one named scenario at a running ADK server.
#
# Every page from Part 2 on generates load with this one script, so the number
# that moves in Cloud Monitoring traces back to a scenario in
# tutorial/scenarios.md, not to an ad-hoc curl. Each scenario owns its city
# mix, its prompts, and its session behavior; there is no ratio flag, because
# the mix belongs to the scenario.
#
# Usage:
#   ./load/turns.sh <scenario> [N]
#
# Scenarios (see tutorial/scenarios.md):
#   baseline        One London turn per fresh session.
#   unknown-city    Half the turns ask for Atlantis (an error status, no raise).
#   slow-tool       Half the turns ask for a 3-day forecast (get_forecast sleeps).
#   multi-city      One turn in four names three cities in a single prompt.
#   growing-context All N turns reuse ONE session, so context accumulates.
#   concurrent      slow-tool and baseline turns fired in parallel, not in order.
#
# Prints one line per turn: scenario, turn index, HTTP status, elapsed seconds.
# So answered turns (status 200) can be counted against exported datapoints.
#
# Env:
#   HOST        server base URL         (default http://localhost:8000)
#   APP_NAME    agent folder / app name (default demo_agent)
#   USER_ID     user id for sessions    (default load-user)
#   EXPORT_WAIT seconds to wait after the last turn so the reader's next
#               export interval (5s) carries the final batch to the backend
#               before you read it back (default 10; set 0 to skip)
#
# The server is `adk web`, `adk api_server`, or `adk deploy cloud_run` output;
# start it first (see the page you came from). `adk web` defaults to port 8000,
# `adk api_server` to 8000 as well; override HOST for Cloud Run.
set -euo pipefail

SCENARIO="${1:?usage: turns.sh <scenario> [N]}"
N="${2:-10}"

HOST="${HOST:-http://localhost:8000}"
APP_NAME="${APP_NAME:-demo_agent}"
USER_ID="${USER_ID:-load-user}"
EXPORT_WAIT="${EXPORT_WAIT:-10}"

# --- one turn -------------------------------------------------------------
# Create a fresh session (or reuse a given id), send one message, print the
# result line. Args: <turn index> <prompt> [session_id].
#   - No session_id: create a new session (baseline's "fresh session per turn").
#   - A session_id given: reuse it (growing-context's one shared session).
send_turn() {
  local idx="$1" prompt="$2" session_id="${3:-}"

  if [[ -z "$session_id" ]]; then
    # POST with no body to the collection endpoint auto-generates the id.
    session_id=$(curl -s -X POST \
      "${HOST}/apps/${APP_NAME}/users/${USER_ID}/sessions" \
      -H 'content-type: application/json' -d '{}' \
      | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
  fi

  # jq is not assumed; build the JSON body with printf and escape the prompt's
  # quotes (the prompts here contain none, but keep it safe).
  local esc_prompt="${prompt//\"/\\\"}"
  local body
  body=$(printf '{"app_name":"%s","user_id":"%s","session_id":"%s","new_message":{"role":"user","parts":[{"text":"%s"}]}}' \
    "$APP_NAME" "$USER_ID" "$session_id" "$esc_prompt")

  local start end elapsed code
  start=$(date +%s.%N)
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${HOST}/run" \
    -H 'content-type: application/json' -d "$body")
  end=$(date +%s.%N)
  elapsed=$(awk "BEGIN{printf \"%.2f\", ${end}-${start}}")

  printf '%-15s turn %3d  http=%s  %ss\n' "$SCENARIO" "$idx" "$code" "$elapsed"
}

# Prompts reused below.
Q_LONDON="What's the weather in London?"
Q_ATLANTIS="What's the weather in Atlantis?"
Q_FORECAST="Give me a 3-day forecast for London."
Q_THREE="What's the weather in London, Tokyo, and New York?"

case "$SCENARIO" in
  baseline)
    # One London turn per fresh session.
    for i in $(seq 1 "$N"); do send_turn "$i" "$Q_LONDON"; done
    ;;

  unknown-city)
    # Half ask for Atlantis; get_weather returns an error status (no raise), so
    # execute_tool.duration gains an error.type series while the turn succeeds.
    for i in $(seq 1 "$N"); do
      if (( i % 2 == 0 )); then send_turn "$i" "$Q_ATLANTIS";
      else send_turn "$i" "$Q_LONDON"; fi
    done
    ;;

  slow-tool)
    # Half ask for a forecast, so get_forecast (0.3-1.5s sleep) runs, mixed with
    # instant London weather turns.
    for i in $(seq 1 "$N"); do
      if (( i % 2 == 0 )); then send_turn "$i" "$Q_FORECAST";
      else send_turn "$i" "$Q_LONDON"; fi
    done
    ;;

  multi-city)
    # One turn in four names three cities in a single prompt; the rest are
    # single-city London turns.
    for i in $(seq 1 "$N"); do
      if (( i % 4 == 0 )); then send_turn "$i" "$Q_THREE";
      else send_turn "$i" "$Q_LONDON"; fi
    done
    ;;

  growing-context)
    # All N turns reuse ONE session, so the model's input tokens climb across
    # the run while output stays flat.
    session_id=$(curl -s -X POST \
      "${HOST}/apps/${APP_NAME}/users/${USER_ID}/sessions" \
      -H 'content-type: application/json' -d '{}' \
      | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
    for i in $(seq 1 "$N"); do send_turn "$i" "$Q_LONDON" "$session_id"; done
    ;;

  concurrent)
    # slow-tool and baseline turns fired in parallel, not in sequence, to check
    # that per-invocation timers do not contaminate each other. Each turn its
    # own session (backgrounded); wait for all before returning.
    for i in $(seq 1 "$N"); do
      if (( i % 2 == 0 )); then send_turn "$i" "$Q_FORECAST" &
      else send_turn "$i" "$Q_LONDON" & fi
    done
    wait
    ;;

  *)
    echo "unknown scenario: ${SCENARIO}" >&2
    echo "one of: baseline unknown-city slow-tool multi-city growing-context concurrent" >&2
    exit 2
    ;;
esac

# The reader exports on a 5s interval, so the last turn's batch has not left the
# process yet. Wait past one more interval before telling the reader to go read.
if (( EXPORT_WAIT > 0 )); then
  printf 'waiting %ss for the final export interval...\n' "$EXPORT_WAIT" >&2
  sleep "$EXPORT_WAIT"
fi
echo "good to go — the series are in Cloud Monitoring" >&2
