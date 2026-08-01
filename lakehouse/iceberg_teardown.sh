#!/usr/bin/env bash
#
# Removes everything iceberg_setup.sh and the tutorial create.
#
# Usage, either way:
#
#   export PROJECT_ID=my-project
#   export BUCKET=my-bucket
#   ./iceberg_teardown.sh
#
#   ./iceberg_teardown.sh PROJECT_ID BUCKET   # arguments win over the env vars
#
#   --revoke-connection-iam  also remove the objectAdmin grant given to the
#                            connection's service account. Off by default
#                            because the connection is often reused.
#
# The bucket itself is never deleted, only the tutorial's folders inside it.

set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: iceberg_teardown.sh [PROJECT_ID BUCKET] [--revoke-connection-iam]

Reads $PROJECT_ID and $BUCKET when arguments are omitted:

  export PROJECT_ID=my-project
  export BUCKET=my-bucket
  ./iceberg_teardown.sh

or pass them directly:

  ./iceberg_teardown.sh my-project my-bucket
USAGE
  exit 1
}

REVOKE_IAM=""
POSITIONAL=()
for ARG in "$@"; do
  case "${ARG}" in
    --revoke-connection-iam) REVOKE_IAM="${ARG}" ;;
    --help|-h)               usage ;;
    *)                       POSITIONAL+=("${ARG}") ;;
  esac
done

PROJECT="${POSITIONAL[0]:-${PROJECT_ID:-}}"
BUCKET="${POSITIONAL[1]:-${BUCKET:-}}"

if [[ -z "${PROJECT}" || -z "${BUCKET}" ]]; then
  [[ -z "${PROJECT}" ]] && echo "ERROR: no project id given (\$PROJECT_ID is unset)." >&2
  [[ -z "${BUCKET}"  ]] && echo "ERROR: no bucket given (\$BUCKET is unset)." >&2
  echo >&2
  usage
fi

BUCKET="${BUCKET#gs://}"
BUCKET="${BUCKET%%/*}"
[[ -n "${BUCKET}" ]] || usage

LOCATION="us"
DATASET="iceberg_lab"
CONNECTION="big_lake_demo"
CATALOG="iceberg_demo"
NAMESPACE="sales"

echo "==> Tearing down Iceberg tutorial resources in ${PROJECT}"
echo

# Order matters: tables before namespaces before catalogs, or the deletes fail
# with "not empty".

echo "==> Dropping tables in the catalog namespace"
for TABLE in orders from_spark spark_written; do
  if gcloud biglake iceberg tables delete "${TABLE}" \
       --catalog="${CATALOG}" --namespace="${NAMESPACE}" \
       --project="${PROJECT}" --quiet >/dev/null 2>&1; then
    echo "    deleted ${NAMESPACE}.${TABLE}"
  fi
done

echo "==> Deleting namespace ${NAMESPACE}"
gcloud biglake iceberg namespaces delete "${NAMESPACE}" \
  --catalog="${CATALOG}" --project="${PROJECT}" --quiet >/dev/null 2>&1 \
  && echo "    deleted" || echo "    not found, skipping"

echo "==> Deleting catalog ${CATALOG}"
gcloud biglake iceberg catalogs delete "${CATALOG}" \
  --project="${PROJECT}" --quiet >/dev/null 2>&1 \
  && echo "    deleted" || echo "    not found, skipping"

echo "==> Deleting dataset ${DATASET} and its tables"
bq --project_id="${PROJECT}" rm -r -f -d "${PROJECT}:${DATASET}" >/dev/null 2>&1 \
  && echo "    deleted" || echo "    not found, skipping"

echo "==> Deleting bucket folders"
for PREFIX in iceberg_lab lakehouse; do
  if gcloud storage rm -r "gs://${BUCKET}/${PREFIX}/" >/dev/null 2>&1; then
    echo "    deleted gs://${BUCKET}/${PREFIX}/"
  else
    echo "    gs://${BUCKET}/${PREFIX}/ not found, skipping"
  fi
done

if [[ "${REVOKE_IAM}" == "--revoke-connection-iam" ]]; then
  echo "==> Revoking connection service account bucket access"
  CONN_SA=$(bq --project_id="${PROJECT}" show --connection --format=json \
    "${PROJECT}.${LOCATION}.${CONNECTION}" 2>/dev/null \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["cloudResource"]["serviceAccountId"])' 2>/dev/null || true)
  if [[ -n "${CONN_SA}" ]]; then
    gcloud storage buckets remove-iam-policy-binding "gs://${BUCKET}" \
      --member="serviceAccount:${CONN_SA}" \
      --role="roles/storage.objectAdmin" \
      --format=none >/dev/null 2>&1 \
      && echo "    revoked for ${CONN_SA}" || echo "    no binding found"
  else
    echo "    connection not found, skipping"
  fi
fi

# The connection itself is left in place. It is cheap, commonly shared with
# other demos, and re-granting bucket IAM is the annoying part to redo.
echo
echo "==> Verifying"

STILL_THERE=0

if bq --project_id="${PROJECT}" show "${PROJECT}:${DATASET}" >/dev/null 2>&1; then
  echo "    WARNING: dataset ${DATASET} still exists"
  STILL_THERE=1
fi

if gcloud biglake iceberg catalogs describe "${CATALOG}" \
     --project="${PROJECT}" >/dev/null 2>&1; then
  echo "    WARNING: catalog ${CATALOG} still exists"
  STILL_THERE=1
fi

for PREFIX in iceberg_lab lakehouse; do
  if gcloud storage ls "gs://${BUCKET}/${PREFIX}/" >/dev/null 2>&1; then
    echo "    WARNING: gs://${BUCKET}/${PREFIX}/ still exists"
    STILL_THERE=1
  fi
done

if [[ "${STILL_THERE}" -eq 0 ]]; then
  echo "    all tutorial resources removed"
else
  echo
  echo "Some resources remain. Delete order matters: tables, then namespaces,"
  echo "then the catalog. Re-run this script, or remove them by hand."
  exit 1
fi
