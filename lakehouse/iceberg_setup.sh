#!/usr/bin/env bash
#
# One-time setup for the BigQuery Iceberg tutorial.
#
# Creates the dataset, the BigLake connection, the Lakehouse runtime catalog,
# and grants the connection's service account write access to the bucket.
#
# Usage, either way:
#
#   export PROJECT_ID=my-project
#   export BUCKET=my-bucket
#   ./iceberg_setup.sh
#
#   ./iceberg_setup.sh PROJECT_ID BUCKET      # arguments win over the env vars
#
#   PROJECT_ID  your Google Cloud project id, e.g. my-project
#   BUCKET      an EXISTING Cloud Storage bucket. Bare name or gs:// URL both
#               work; a trailing slash is fine too. The bucket must already
#               exist and be in the same location as the dataset (us).
#
# To create a dedicated bucket first:
#   gcloud storage buckets create gs://my-iceberg-lab \
#     --project=my-project --location=us

set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: iceberg_setup.sh [PROJECT_ID BUCKET]

Reads $PROJECT_ID and $BUCKET when arguments are omitted:

  export PROJECT_ID=my-project
  export BUCKET=my-bucket
  ./iceberg_setup.sh

or pass them directly:

  ./iceberg_setup.sh my-project my-bucket
  ./iceberg_setup.sh my-project gs://my-iceberg-lab
USAGE
  exit 1
}

# Arguments take precedence; otherwise fall back to the environment.
PROJECT="${1:-${PROJECT_ID:-}}"
BUCKET="${2:-${BUCKET:-}}"

if [[ -z "${PROJECT}" || -z "${BUCKET}" ]]; then
  [[ -z "${PROJECT}" ]] && echo "ERROR: no project id given (\$PROJECT_ID is unset)." >&2
  [[ -z "${BUCKET}"  ]] && echo "ERROR: no bucket given (\$BUCKET is unset)." >&2
  echo >&2
  usage
fi

# Accept gs://name, gs://name/, or a bare name. Everything below builds its own
# gs:// URLs, so normalize to the bare bucket name here.
BUCKET="${BUCKET#gs://}"
BUCKET="${BUCKET%%/*}"

if [[ -z "${BUCKET}" ]]; then
  echo "ERROR: bucket name is empty after normalizing '$2'." >&2
  usage
fi

echo "==> Project: ${PROJECT}"
echo "==> Bucket:  gs://${BUCKET}"

# Fail early with a clear message rather than midway through setup.
if ! gcloud storage buckets describe "gs://${BUCKET}" \
     --project="${PROJECT}" --format="value(name)" >/dev/null 2>&1; then
  echo "ERROR: gs://${BUCKET} does not exist or you cannot access it." >&2
  echo "Create it with:" >&2
  echo "  gcloud storage buckets create gs://${BUCKET} \\" >&2
  echo "    --project=${PROJECT} --location=us" >&2
  exit 1
fi

LOCATION="us"
DATASET="iceberg_lab"
CONNECTION="big_lake_demo"
CATALOG="iceberg_demo"
NAMESPACE="sales"

echo "==> Enabling APIs"
gcloud services enable \
  bigquery.googleapis.com \
  bigqueryconnection.googleapis.com \
  biglake.googleapis.com \
  dataproc.googleapis.com \
  storage.googleapis.com \
  --project="${PROJECT}"

echo "==> Creating dataset ${DATASET}"
bq --project_id="${PROJECT}" --location="${LOCATION}" mk --force --dataset "${DATASET}"

echo "==> Creating BigLake (cloud resource) connection ${CONNECTION}"
if ! bq --project_id="${PROJECT}" show --connection \
     "${PROJECT}.${LOCATION}.${CONNECTION}" >/dev/null 2>&1; then
  bq --project_id="${PROJECT}" mk --connection \
    --location="${LOCATION}" \
    --connection_type=CLOUD_RESOURCE \
    "${CONNECTION}"
else
  echo "    connection already exists, skipping"
fi

# The connection has its own service account. It is this identity, not yours,
# that reads and writes the Iceberg files in the bucket.
CONN_SA=$(bq --project_id="${PROJECT}" show --connection --format=json \
  "${PROJECT}.${LOCATION}.${CONNECTION}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["cloudResource"]["serviceAccountId"])')

echo "==> Connection service account: ${CONN_SA}"
echo "==> Granting it objectAdmin on gs://${BUCKET}"
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${CONN_SA}" \
  --role="roles/storage.objectAdmin" \
  --format=none

echo "==> Creating Lakehouse runtime catalog ${CATALOG}"
if ! gcloud biglake iceberg catalogs describe "${CATALOG}" \
     --project="${PROJECT}" >/dev/null 2>&1; then
  gcloud biglake iceberg catalogs create "${CATALOG}" \
    --catalog-type=lakehouse \
    --default-location="gs://${BUCKET}/lakehouse" \
    --project="${PROJECT}"
else
  echo "    catalog already exists, skipping"
fi

echo "==> Creating namespace ${NAMESPACE} in ${CATALOG}"
if ! gcloud biglake iceberg namespaces describe "${NAMESPACE}" \
     --catalog="${CATALOG}" --project="${PROJECT}" >/dev/null 2>&1; then
  gcloud biglake iceberg namespaces create "${NAMESPACE}" \
    --catalog="${CATALOG}" \
    --project="${PROJECT}"
else
  echo "    namespace already exists, skipping"
fi

# Querying catalog tables from BigQuery requires BigLake permissions. Granting
# this needs project IAM admin rights; run it yourself if the tutorial's
# four-part names fail to resolve.
cat <<EOF

==> Setup complete.

  Dataset     ${PROJECT}:${DATASET}
  Connection  ${PROJECT}.${LOCATION}.${CONNECTION}
  Catalog     ${CATALOG}  (default location gs://${BUCKET}/lakehouse)
  Namespace   ${NAMESPACE}

Next: work through ICEBERG_TUTORIAL.md. Keep these set in your shell, and the
SQL file can be rendered with real values by iceberg_sql.sh:

  export PROJECT_ID=${PROJECT}
  export BUCKET=${BUCKET}

  ./iceberg_sql.sh                # print the SQL with values filled in
  ./iceberg_sql.sh 'insert query'  # print just one statement

If four-part table names (${PROJECT}.${CATALOG}.${NAMESPACE}.table) do not
resolve in BigQuery, grant yourself BigLake Admin:

  gcloud projects add-iam-policy-binding ${PROJECT} \\
    --member="user:\$(gcloud config get-value account)" \\
    --role="roles/biglake.admin"

To remove everything this created, see the Cleanup section of the tutorial or
run ./iceberg_teardown.sh ${PROJECT} ${BUCKET}

EOF
