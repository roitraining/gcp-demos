# Iceberg on BigQuery

> **Under construction.** This tutorial is a work in progress. Parts of it have
> been run end to end against a real project, but several sections have not, and
> the teardown script has a known bug that can report success without deleting
> anything. See [Status](#status) before using it with an audience.

A hands-on walkthrough of the three different things BigQuery calls "Iceberg,"
and how they differ in the one way that actually matters: who owns the table
metadata.

|                       | Metadata owner                           | BigQuery writes? | Spark writes?            | Status |
| --------------------- | ---------------------------------------- | ---------------- | ------------------------ | ------ |
| **Managed**           | BigQuery's own metastore                 | Yes, full DML    | Yes, via the Storage API | GA     |
| **Lakehouse catalog** | Lakehouse runtime catalog (Iceberg REST) | Yes (Preview)    | Yes, GA                  | Mixed  |
| **External**          | Nobody, self-managed files               | No, read-only    | Yes, it owns them        | GA     |

All three store Parquet in your own Cloud Storage bucket. "Iceberg" names the
file format, which is why it shows up in all three names and distinguishes none
of them. The tutorial's aim is to make that distinction concrete: you create one
of each, write to them from both BigQuery and Spark, and watch which writes are
accepted and which are refused.

## Contents

| File                   | What it is                                            |
| ---------------------- | ----------------------------------------------------- |
| `ICEBERG_TUTORIAL.md`  | The tutorial itself; start here                       |
| `iceberg_setup.sh`     | One-time setup: dataset, connection, catalog, IAM     |
| `iceberg_tutorial.sql` | Every SQL statement, in order                         |
| `iceberg_sql.sh`       | Prints the SQL with your project and bucket filled in |
| `iceberg_spark.ipynb`  | BigQuery Studio notebook for the Spark half           |
| `iceberg_teardown.sh`  | Removes what the tutorial creates (see Status)        |

## Quick start

You need a Google Cloud project and an existing Cloud Storage bucket in the `us`
location.

```bash
export PROJECT_ID=my-project
export BUCKET=my-bucket
./iceberg_setup.sh
```

Then work through `ICEBERG_TUTORIAL.md`. Setup creates the `iceberg_lab`
dataset, a BigLake connection named `big_lake_demo`, the Lakehouse runtime
catalog `iceberg_demo` with namespace `sales`, and grants the connection's
service account write access to the bucket. Re-running it is safe.

To clean up afterwards:

```bash
./iceberg_teardown.sh
```

## Status

Verified by running end to end against a real project:

- Managed table create, `INSERT`/`UPDATE`/`DELETE`, GCS layout, and
  `EXPORT TABLE METADATA` output
- The bucket IAM failure and its fix
- External table create, query, read-only rejection, and the pinned-snapshot
  staleness demo
- Catalog and namespace creation, confirmed live over the REST endpoint
- Spark needs `iceberg-spark-runtime-3.5_2.12:1.9.1`; without exported metadata
  it fails with `Cannot parse missing int: format-version`

Not yet verified, and flagged inline in the tutorial where they appear:

- The four-part `CREATE TABLE` from BigQuery (see the Known gap box)
- The notebook end to end, written after switching from Dataproc batch
  submission to BigQuery Studio sessions
- The console click-throughs in Parts 1 and 3, written from the dialog's field
  labels rather than from running them

### Known bug: teardown can report false success

`iceberg_teardown.sh` redirects stderr to `/dev/null` on every delete and every
verification check. Any failure, including an expired auth token or a wrong
project id, is therefore indistinguishable from "the resource isn't there," and
the script prints `not found, skipping` for each step and then
`all tutorial resources removed` while the resources are still live.

If teardown reports success, confirm it before believing it:

```bash
gcloud biglake iceberg catalogs list --project=$PROJECT_ID
bq --project_id=$PROJECT_ID ls
gcloud storage ls gs://$BUCKET/
```

A stale credential is the most common cause; `gcloud auth login` and re-running
usually clears it. Deleting by hand also works, but **order matters**: tables,
then namespaces, then the catalog. Deleting a catalog that still has namespaces
fails, and dropping tables in BigQuery does not remove the namespace or the
catalog.

Fixes planned for the script: distinguish a genuine 404 from other errors rather
than swallowing both, fail fast when the project is unreachable, treat an
unverifiable check as failure instead of success, and delete tables by listing
the namespace rather than from a hardcoded list.

## Notes

The bucket and the `big_lake_demo` connection are intentionally left in place by
teardown. The connection is cheap, is often shared with other demos, and
re-granting its bucket IAM is the tedious part to redo. To revoke that grant
too:

```bash
./iceberg_teardown.sh --revoke-connection-iam
```

The IAM grant is the step people most often miss. A BigLake connection has
**its own** service account, and it is that identity, not yours, that writes
Iceberg files to the bucket. Without the grant, creating a managed table fails
with a message about the bucket not being accessible via appropriate IAM roles.
