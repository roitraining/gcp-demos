#!/usr/bin/env bash
#
# Prints iceberg_tutorial.sql with PROJECT_ID and BUCKET filled in, so you can
# copy statements straight into the BigQuery console without editing them.
#
# Usage:
#   export PROJECT_ID=my-project
#   export BUCKET=my-bucket
#
#   ./iceberg_sql.sh                    # the whole file, values substituted
#   ./iceberg_sql.sh 'insert query'     # just that one statement
#   ./iceberg_sql.sh --list             # names of every statement
#
# Statements are delimited by "-- NAME query" comments in iceberg_tutorial.sql.

set -euo pipefail

SQL_FILE="$(dirname "$0")/iceberg_tutorial.sql"

usage() {
  cat >&2 <<'USAGE'
usage: iceberg_sql.sh [--list | STATEMENT_NAME]

Requires $PROJECT_ID and $BUCKET:

  export PROJECT_ID=my-project
  export BUCKET=my-bucket

  ./iceberg_sql.sh                   # whole file with values substituted
  ./iceberg_sql.sh 'insert query'    # one statement
  ./iceberg_sql.sh --list            # list statement names
USAGE
  exit 1
}

[[ -f "${SQL_FILE}" ]] || { echo "ERROR: ${SQL_FILE} not found." >&2; exit 1; }

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
fi

if [[ "${1:-}" == "--list" ]]; then
  grep -oE '^-- [a-z0-9 ]+ query$' "${SQL_FILE}" | sed 's/^-- //'
  exit 0
fi

PROJECT="${PROJECT_ID:-}"
BUCKET_NAME="${BUCKET:-}"

if [[ -z "${PROJECT}" || -z "${BUCKET_NAME}" ]]; then
  [[ -z "${PROJECT}"     ]] && echo "ERROR: \$PROJECT_ID is unset." >&2
  [[ -z "${BUCKET_NAME}" ]] && echo "ERROR: \$BUCKET is unset." >&2
  echo >&2
  usage
fi

BUCKET_NAME="${BUCKET_NAME#gs://}"
BUCKET_NAME="${BUCKET_NAME%%/*}"

# Reads stdin. BSD sed does not accept "-" as a filename, so never pass one.
render() {
  sed -e "s|PROJECT_ID|${PROJECT}|g" -e "s|BUCKET|${BUCKET_NAME}|g"
}

if [[ $# -eq 0 ]]; then
  render < "${SQL_FILE}"
  exit 0
fi

# Print a single statement: from its "-- NAME query" marker up to the line
# before the next marker or section divider.
NAME="$1"

if ! grep -qxF -- "-- ${NAME}" "${SQL_FILE}"; then
  echo "ERROR: no statement named '${NAME}'." >&2
  echo "Run './iceberg_sql.sh --list' to see the available names." >&2
  exit 1
fi

awk -v want="-- ${NAME}" '
  $0 == want { printing = 1 }
  printing && /^-- -+$/ { exit }
  printing && /^-- [a-z0-9 ]+ query$/ && $0 != want { exit }
  printing { print }
' "${SQL_FILE}" | render
