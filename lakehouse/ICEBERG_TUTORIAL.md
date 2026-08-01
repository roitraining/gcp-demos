# Three kinds of Iceberg table in BigQuery

BigQuery uses the word "Iceberg" for three different things. They look similar in
the **Create table** dialog and in the docs, but they differ in the one way that
matters: **who owns the metadata**. Everything else, including who can write,
follows from that.

|                       | Metadata owner                           | BigQuery writes? | Spark writes?                          | Status |
| --------------------- | ---------------------------------------- | ---------------- | -------------------------------------- | ------ |
| **Managed**           | BigQuery's own metastore                 | Yes, full DML    | Yes, via the Storage API               | GA     |
| **Lakehouse catalog** | Lakehouse runtime catalog (Iceberg REST) | Yes (Preview)    | Yes, GA                                | Mixed  |
| **External**          | Nobody, self-managed files               | No, read-only    | Yes, it owns them                      | GA     |

Managed tables have a second, weaker access path: reading the exported Iceberg
files directly, which is read-only and lags behind the live table. Part 1 covers
both and explains when each applies.

All three store data as Parquet in your own Cloud Storage bucket. "Iceberg" names
the file format, which is why it appears in all three names and distinguishes none
of them.

## Files

| File                   | What it is                                        |
| ---------------------- | ------------------------------------------------- |
| `iceberg_setup.sh`     | One-time setup: dataset, connection, catalog, IAM |
| `iceberg_tutorial.sql` | Every SQL statement, in order                     |
| `iceberg_spark.ipynb`  | BigQuery Studio notebook for the Spark half       |
| `iceberg_sql.sh`       | Prints the SQL with your project and bucket filled in |
| `iceberg_teardown.sh`  | Removes everything the tutorial creates           |

## Setup

### 1. Set two environment variables

Everything below reads these, so set them once and the rest of the tutorial is
copy-paste:

```bash
export PROJECT_ID=my-project
export BUCKET=my-bucket
```

`BUCKET` accepts either `my-bucket` or `gs://my-bucket`; the scripts
strip the prefix. Use your own values. The bucket does not have to be named
after the project; it just has to exist and be in the `us` location.

### 2. Create a bucket if you need one

It must already exist and be in the `us` location:

```bash
gcloud storage buckets create gs://$BUCKET --project=$PROJECT_ID --location=us
```

### 3. Run setup

```bash
./iceberg_setup.sh
```

Both scripts also take arguments, which override the environment:

```bash
./iceberg_setup.sh my-project gs://some-other-bucket
```

### 4. Get SQL with your values already substituted

`iceberg_tutorial.sql` is written with `PROJECT_ID` and `BUCKET` placeholders.
Rather than editing it, print the filled-in version:

```bash
./iceberg_sql.sh --list                        # every statement name
./iceberg_sql.sh 'create managed table query'  # one statement, ready to paste
./iceberg_sql.sh                               # the whole file
```

For example:

```console
$ ./iceberg_sql.sh 'create managed table query'
-- create managed table query
CREATE OR REPLACE TABLE `my-project.iceberg_lab.orders_managed` (
  order_id INT64,
  ...
```

Each part below names the statement it needs, so you can paste straight into the
BigQuery console.

### Where each block runs

Three places, and the code fences say which:

| Block | Where it runs |
|---|---|
| ```` ```sql ```` | The **BigQuery console query editor**. Open BigQuery Studio and click **+ Compose a new query**. |
| ```` ```bash ```` | Your shell, Cloud Shell or local, with `gcloud` and `bq` authenticated. |
| Notebook cells | `iceberg_spark.ipynb`, in a BigQuery Studio notebook. Called out explicitly where they come up. |

`EXPORT TABLE METADATA` in Part 1 is the one that trips people up: it looks like
an admin command but it is plain BigQuery SQL and runs in the query editor.

### What setup creates

It creates the `iceberg_lab` dataset, a BigLake connection named
`big_lake_demo`, the Lakehouse runtime catalog `iceberg_demo` with namespace
`sales`, and grants the connection's service account write access to the bucket.
Re-running it is safe; anything that already exists is skipped.

That IAM grant is the one people miss. A BigLake connection has **its own**
service account, and it is that identity, not yours, that writes Iceberg files.
Without the grant, creating a managed table fails with:

```
Please make sure gs://BUCKET/... is accessible via appropriate IAM roles
(Storage Admin or Legacy Bucket Writer) and within VPC-SC perimeter.
```

Note that the grant covers the whole bucket, not a prefix. On a bucket shared
with other work, that gives the connection write access to everything in it,
which is a good reason to use a dedicated bucket.

---

## Part 1: Managed Iceberg tables

BigQuery owns the metadata and does the writing. You get full DML, the Storage
Write API, and automatic compaction, but the data sits in your bucket in open
format rather than BigQuery's proprietary storage.

### Create it in the console

The **Create table** dialog is reached from the dataset, not from a top-level
menu, which is the part that is easy to miss.

1. Open [BigQuery Studio](https://console.cloud.google.com/bigquery).
2. In the **Explorer** panel on the left, expand your project. If you do not see
   it, click **+ ADD** > **Star a project by name**.
3. Expand the project and find the `iceberg_lab` dataset that setup created.
4. Hover over `iceberg_lab`, click the **⋮** (three dots) that appears, and
   choose **Create table**.

Now fill in the dialog:

| Field | Value |
|---|---|
| Field | Value |
|---|---|
| **Create table from** | **Empty table** |
| **Project** | your project |
| **Dataset** | `iceberg_lab` |
| **Table** | `orders_managed_ui` |
| **Table type** | leave as **Empty table** |
| **Create a BigQuery table for Apache Iceberg** | **tick this** |

Ticking that box is what makes it an Iceberg table. You cannot pick "Apache
Iceberg" from the **Table type** dropdown; the checkbox is the control, and
ticking it reveals the rest of the fields:

| Field | Value |
|---|---|
| **Connection ID** | `us.big_lake_demo` |
| **gs:// Storage URI** | type `YOUR_BUCKET/iceberg_lab/orders_managed_ui` (see note below) |
| **File format** | **PARQUET** |
| **Table format** | **ICEBERG** |

Two things about the storage URI. The field already shows `gs://`, so do not type
it again. And the folder does **not** exist yet, so there is nothing to browse to
and no **Browse** button will find it. Type the path; BigQuery creates it when it
creates the table. Only the bucket has to exist.

Under **Schema**, click **Edit as text** and paste:

```
order_id:INTEGER,customer:STRING,amount:NUMERIC,order_date:DATE
```

Then click **CREATE TABLE**.

Now look at the bucket and you will see the folder BigQuery just made:

```bash
gcloud storage ls -r gs://$BUCKET/iceberg_lab/orders_managed_ui/
```

Note the table name is `orders_managed_ui`, not `orders_managed`. The rest of the
tutorial uses `orders_managed`, created below in SQL, so this one is only to see
what the dialog asks for. Drop it when you are done, or keep it to compare.

**Connection ID** is worth pausing on, because it appears here and again on the
external table in Part 3. Either way BigQuery needs the connection's service
identity to reach your bucket. Same field, very different ownership.

### Create it in SQL

`./iceberg_sql.sh 'create managed table query'`

```sql
CREATE OR REPLACE TABLE `PROJECT_ID.iceberg_lab.orders_managed` (
  order_id INT64,
  customer STRING,
  amount NUMERIC,
  order_date DATE
)
WITH CONNECTION `PROJECT_ID.us.big_lake_demo`
OPTIONS (
  file_format = 'PARQUET',
  table_format = 'ICEBERG',
  storage_uri = 'gs://BUCKET/iceberg_lab/orders_managed'
);
```

### Create it with the CLI

`bq mk` takes the same four options the dialog asks for, as flags:

```bash
bq mk --table \
  --connection_id=$PROJECT_ID.us.big_lake_demo \
  --file_format=PARQUET \
  --table_format=ICEBERG \
  --storage_uri="gs://$BUCKET/iceberg_lab/orders_managed_cli" \
  $PROJECT_ID:iceberg_lab.orders_managed_cli \
  order_id:INTEGER,customer:STRING,amount:NUMERIC,order_date:DATE
```

```
Table 'PROJECT:iceberg_lab.orders_managed_cli' successfully created.
```

Same table, three ways. The console is the discoverable route, `bq mk` suits
scripting, and SQL is the one to teach because the options are visible in the
statement rather than hidden behind flags or a dialog.

Drop the two extras when you have compared them:

```bash
bq rm -f -t $PROJECT_ID:iceberg_lab.orders_managed_ui
bq rm -f -t $PROJECT_ID:iceberg_lab.orders_managed_cli
```

### Write to it

```bash
./iceberg_sql.sh 'insert query'
./iceberg_sql.sh 'update query'
./iceberg_sql.sh 'delete query'
```

All three work. This is the whole point of a managed table, and it is what an
external table cannot do.

### Look at the bucket

```bash
gcloud storage ls -r gs://$BUCKET/iceberg_lab/orders_managed/
```

You get a `data/` folder of Parquet files and a `metadata/` folder. Open the
metadata file:

```bash
gcloud storage cat gs://$BUCKET/iceberg_lab/orders_managed/metadata/v0.metadata.json
```

```json
{"properties":{"bigquery-table-id":"PROJECT.iceberg_lab.orders_managed"},
 "current-snapshot-id":-1}
```

That is a **stub**. No schema, no snapshot, just a pointer back to BigQuery. After
three DML statements it has not changed. A managed table does not continuously
publish Iceberg metadata, because BigQuery's metastore is the source of truth and
the files in the bucket are an export target.

### Make it readable by Spark

Run this in the **BigQuery console query editor**, the same place as every other
statement so far (`./iceberg_sql.sh 'export metadata query'`):

```sql
EXPORT TABLE METADATA FROM `PROJECT_ID.iceberg_lab.orders_managed`;
```

It is ordinary BigQuery SQL, not a Spark or `gcloud` command, and it takes a
second or two. There is no result set; success shows as "This statement created
no output" or a completed job with no rows.

Check the bucket again and compare it to what was there before:

```bash
gcloud storage ls gs://$BUCKET/iceberg_lab/orders_managed/metadata/
```

The stub `v0.metadata.json` is still there, but now it has company: a
`vNNNNNNNNNN.metadata.json` with a genuine `current-snapshot-id`, Avro manifest
files, and `version-hint.text`. That last file is how Iceberg readers find the
current version.

Skip this step and Spark fails with:

```
IllegalArgumentException: Cannot parse missing int: format-version
```

Which is a confusing way for Iceberg to say "this is not an Iceberg table."

### Do you really have to export after every write?

By default, yes: the export is manual, and the snapshot Spark reads is only as
fresh as the last `EXPORT TABLE METADATA`. That is what makes the demo above
work. But manual is not the only option, and it would be a bad recommendation for
production:

| Approach | How | Freshness |
|---|---|---|
| Manual export | `EXPORT TABLE METADATA` by hand | Whenever you remember |
| Scheduled query | The same statement as a [scheduled query](https://docs.cloud.google.com/bigquery/docs/scheduling-queries), e.g. `--schedule='every 24 hours'` | As fresh as the interval |
| Auto-refresh | Enabled per project by emailing `bigquery-tables-for-apache-iceberg-help@google.com` | Every table mutation |

All three are documented under "Create Iceberg managed table metadata snapshots"
in [Apache Iceberg managed tables](https://docs.cloud.google.com/bigquery/docs/biglake-iceberg-tables-in-bigquery).
On auto-refresh, that page says: "Enable metadata auto-refresh for your project to
automatically update your Iceberg table metadata snapshot on each table mutation."

So the honest version is: metadata export is manual **by default**, schedulable
with ordinary scheduled queries, and can be made automatic per project. Teach the
manual form because it makes the mechanism visible, then say the other two exist.

The underlying point survives either way. Spark reads an exported snapshot of the
metadata, not BigQuery's live state, so there is always a refresh step between a
BigQuery write and Spark seeing it. Auto-refresh shortens that gap; it does not
remove the indirection. Part 2's catalog does.

### Read and write it from Spark

Open `iceberg_spark.ipynb` in BigQuery Studio and run section 2. Spark reaches a
managed table two different ways, and the choice matters:

| | BigQuery Storage API | Iceberg libraries |
|---|---|---|
| Spark format | `.format("bigquery")` | `.format("iceberg")` |
| Reaches the table by | gRPC to BigQuery | reading files in the bucket |
| Needs `EXPORT TABLE METADATA` | no | **yes** |
| Sees | live table state | the last exported snapshot |
| Spark can write | **yes**, `writeMethod=direct` | no |

Use the Storage API. It is live, read-write, and has no export step to forget:

```python
df = spark.read.format("bigquery").load(f"{PROJECT}.iceberg_lab.orders_managed")

new_rows.write.format("bigquery") \
    .option("writeMethod", "direct") \
    .mode("append") \
    .save(f"{PROJECT}.iceberg_lab.orders_managed")
```

`writeMethod=direct` goes through the Storage Write API over gRPC rather than
staging files in GCS first. BigQuery stays the arbiter of table state, so Spark is
simply another client and the write is visible in the console immediately.

The file-based route is worth seeing once, because it explains what
`EXPORT TABLE METADATA` is for. There Spark reads `version-hint.text`, then the
metadata JSON, then the manifests, then the Parquet files, with **no catalog
server anywhere in the path**. That is Iceberg's filesystem-as-catalog
arrangement, and it is why that route is read-only and goes stale: nothing is
tracking commits except a text file in a bucket.

The takeaway: Spark sees an exported snapshot, not live BigQuery state. Something
has to refresh that snapshot between a BigQuery write and Spark seeing it, whether
you run the export by hand, schedule it, or have auto-refresh enabled.
Interoperability here is real, but it is one-way and it goes through an export.

---

## Part 2: Lakehouse runtime catalog tables

This is the newest of the three and the one that fixes Part 1's export dance. The
Lakehouse runtime catalog is a regional metadata service that speaks the standard
**Iceberg REST catalog** protocol. BigQuery, Spark, Trino, and Flink all connect
to the same catalog, so there is no export step and no stale snapshot.

Tables use **four-part names**:

```
PROJECT_NAME.CATALOG_ID.NAMESPACE.TABLE_NAME
```

`CATALOG_ID` is a real resource created with `gcloud biglake iceberg catalogs
create` (the setup script does this). It is not a BigQuery dataset. This is the
key point of confusion: a BigQuery dataset and a catalog namespace are different
things living in different systems.

### Create the table from BigQuery

```sql
CREATE TABLE `PROJECT_ID.iceberg_demo.sales.orders` (id INT64, data STRING);
```

Per the docs, tables created this way get BigQuery DML and automatic table
management enabled by default.

> ### ⚠️ Known gap: verify this step before teaching it
>
> **This statement did not resolve during authoring.** From `bq` CLI 2.1.36 it
> fails with:
>
> ```
> Not found: Dataset PROJECT:iceberg_demo.sales was not found in location US
> ```
>
> BigQuery is parsing `iceberg_demo.sales` as a two-part dataset name instead of
> catalog + namespace. What was verified: the catalog and namespace both exist and
> resolve correctly through the REST endpoint
> (`bl://projects/PROJECT/catalogs/iceberg_demo` lists namespace `sales`).
>
> Two likely causes, untested:
>
> 1. **Missing IAM.** The docs list BigLake Admin (`roles/biglake.admin`) as a
>    prerequisite. Grant it and retry:
>    ```bash
>    gcloud projects add-iam-policy-binding PROJECT_ID \
>      --member="user:$(gcloud config get-value account)" \
>      --role="roles/biglake.admin"
>    ```
> 2. **Client support.** BigQuery read/write against the runtime catalog is in
>    **Preview**, and preview surfaces often reach the console before the API path
>    `bq` uses. Try the same statement in the BigQuery console first, since that is
>    where students will run it anyway.
>
> Everything else in Part 2, including the whole notebook section, runs against
> Spark and does not depend on this statement. If it turns out the BigQuery side
> is not available in your project yet, teach Part 2 as Spark-first and use the
> BigQuery half as the "where this is heading" story.

### Read and write it from Spark

Notebook section 3. Spark registers the catalog by name:

```python
props["spark.sql.catalog.lakehouse.type"] = "rest"
props["spark.sql.catalog.lakehouse.uri"] = \
    "https://biglake.googleapis.com/iceberg/v1/restcatalog"
props["spark.sql.catalog.lakehouse.warehouse"] = \
    f"bl://projects/{PROJECT}/catalogs/{CATALOG}"
```

Then `lakehouse.sales.orders` is just a table. Insert from Spark, query from
BigQuery, and the row is there with no export. Create a table in Spark and it
appears in BigQuery under the same four-part name.

That round trip is the argument for this table type, and it is why Google
recommends the runtime catalog for new lakehouse work.

---

## Part 3: External Iceberg tables

The oldest and simplest: somebody else owns the Iceberg table, and BigQuery reads
it. Read-only, always.

### Create it in the console

Before you start, get the metadata filename you will point at:

```bash
gcloud storage ls gs://$BUCKET/iceberg_lab/orders_managed/metadata/
```

Copy the path of the `vNNNNNNNNNN.metadata.json` file, not `v0.metadata.json`
and not `version-hint.text`.

Same route as Part 1: **Explorer** > expand your project > hover `iceberg_lab` >
**⋮** > **Create table**.

| Field | Value |
|---|---|
| **Create table from** | **Google Cloud Storage** |
| **Select file from GCS bucket** | the metadata path, without `gs://` (the field supplies it) |
| **File format** | **Iceberg** |
| **Project** | your project |
| **Dataset** | `iceberg_lab` |
| **Table** | `orders_external_ui` |
| **Table type** | **External table** |
| **Create a Lakehouse table using a Cloud resource connection** | **tick this** |
| **Connection ID** | `us.big_lake_demo` |

Then click **CREATE TABLE**.

This is the dialog's other personality. Compare it to Part 1: **Table type** is
now **External table**, there is no storage URI to write to, and no schema to
enter, because the Iceberg metadata already describes the columns. You are
registering somebody else's table, not making one.

### Create it in SQL

`./iceberg_sql.sh 'create external table query'`

```sql
CREATE OR REPLACE EXTERNAL TABLE `PROJECT_ID.iceberg_lab.orders_external`
WITH CONNECTION `PROJECT_ID.us.big_lake_demo`
OPTIONS (
  format = 'ICEBERG',
  uris = ['gs://BUCKET/iceberg_lab/orders_managed/metadata/vNNNNNNNNNN.metadata.json']
);
```

Note what `uris` points at: **one specific metadata JSON file**. Not a folder, not
a table, a single snapshot. Get the current filename with:

```bash
gcloud storage ls gs://$BUCKET/iceberg_lab/orders_managed/metadata/
```

For this walkthrough you can point it at the managed table from Part 1, which is
convenient and makes the next two demos sharp. In real use the writer is Spark,
Flink, or another engine.

### Prove it is read-only

```sql
INSERT INTO `PROJECT_ID.iceberg_lab.orders_external` VALUES (99, 'nope', 0.00, CURRENT_DATE());
```

```
DML statements are only supported over tables that have data stored in
BigQuery. Unsupported table: PROJECT:iceberg_lab.orders_external
```

### Prove the snapshot is pinned

Add a row to the managed table, then count both:

```sql
INSERT INTO `PROJECT_ID.iceberg_lab.orders_managed`
VALUES (4, 'umbrella', 500.00, DATE '2026-01-18');

SELECT 'managed'  AS which, COUNT(*) AS n FROM `PROJECT_ID.iceberg_lab.orders_managed`
UNION ALL
SELECT 'external' AS which, COUNT(*) AS n FROM `PROJECT_ID.iceberg_lab.orders_external`;
```

```
which     n
managed   3
external  2
```

Same underlying data, different answers. The external table is still reading the
metadata file it was created with. To catch up you re-run `EXPORT TABLE METADATA`
and recreate the external table pointing at the new file.

This is the single most important thing to know about external Iceberg tables, and
it is the reason the runtime catalog in Part 2 exists.

### Read it from Spark

Nothing new: an external table is an Iceberg table in a bucket, which is what the
notebook already read in Part 1. Notebook section 4 does the more interesting
direction, writing a table from Spark and pointing BigQuery at it.

---

## How to choose

- **Managed** when BigQuery is the primary engine and you want DML and automatic
  optimization, but need the data in open format in your own bucket. Other engines
  can still read *and write* it through the BigQuery Storage API, so "managed"
  does not mean "BigQuery only."
- **Lakehouse catalog** when several engines share the same tables and you would
  rather not depend on a Google-specific connector. Any Iceberg-compatible engine
  can join over the standard REST protocol. Mind the Preview status on the
  BigQuery side.
- **External** when another system owns the data and you only need to query it.
  Best for staging and legacy read-only cases.

The distinction between the first two is easy to get backwards. It is not that
only the catalog allows Spark to write, because the Storage API allows that
against managed tables today. It is *how* an engine connects: a Google connector
speaking to BigQuery, versus an open protocol any Iceberg client can speak.

## Cleanup

```bash
./iceberg_teardown.sh
```

This drops the catalog tables, the `sales` namespace, the `iceberg_demo` catalog,
the `iceberg_lab` dataset, and the tutorial's folders in the bucket, then verifies
each one is actually gone and exits non-zero if anything survived.

The bucket itself is never deleted, and neither is the `big_lake_demo` connection,
since it is commonly shared with other demos and re-granting its bucket IAM is the
tedious part to redo. To revoke that grant as well:

```bash
./iceberg_teardown.sh --revoke-connection-iam
```

Deleting by hand is easy to get wrong, because **order matters**: tables, then
namespaces, then the catalog. Deleting a catalog that still has namespaces fails,
and dropping the tables in BigQuery does not remove the namespace or the catalog.
It is also worth knowing that catalog namespaces show up in the BigQuery console
next to datasets but are **not** datasets, so `bq rm` will not touch them.

## Verification status

Verified by running end to end against a real project:

- Managed table create, `INSERT`/`UPDATE`/`DELETE`, GCS layout, the stub
  `v0.metadata.json`, and `EXPORT TABLE METADATA` output
- The bucket IAM failure and its fix
- External table create, query, read-only rejection, and the pinned-snapshot
  staleness demo
- Catalog and namespace creation, confirmed live over the REST endpoint
- Spark needs `iceberg-spark-runtime-3.5_2.12:1.9.1`; without exported metadata it
  fails with `Cannot parse missing int: format-version`

Not verified, flagged inline:

- The four-part `CREATE TABLE` from BigQuery (see the Known gap box)
- The notebook end to end, which was written after switching from Dataproc batch
  submission to BigQuery Studio sessions
- The console click-throughs in Parts 1 and 3, written from the dialog's field
  labels rather than from running them

## References

- [Apache Iceberg managed tables](https://docs.cloud.google.com/bigquery/docs/biglake-iceberg-tables-in-bigquery)
  covers managed tables, `EXPORT TABLE METADATA`, and the three metadata refresh
  approaches under "Create Iceberg managed table metadata snapshots"
- [Create Apache Iceberg external tables](https://docs.cloud.google.com/bigquery/docs/iceberg-external-tables)
  for the read-only external table and its `uris` metadata pointer
- [Understand table types and capabilities](https://docs.cloud.google.com/biglake/docs/about-lakehouse-iceberg-rest-catalog-tables)
  is the clearest side-by-side of the three types and what is GA vs Preview
- [Query tables using SQL](https://docs.cloud.google.com/lakehouse/docs/query-table)
  documents the four-part `PROJECT.CATALOG.NAMESPACE.TABLE` naming
- [Set up the Lakehouse Iceberg REST catalog endpoint](https://docs.cloud.google.com/biglake/docs/blms-rest-catalog)
  has the Spark catalog properties used in the notebook
- [Use Spark in BigQuery](https://docs.cloud.google.com/bigquery/docs/use-spark)
  for the `DataprocSparkSession` builder the notebook uses
- [spark-bigquery-connector](https://github.com/GoogleCloudDataproc/spark-bigquery-connector)
  for `.format("bigquery")`, `writeMethod=direct`, and `writeAtLeastOnce`
- [Lakehouse tables](https://docs.cloud.google.com/lakehouse/docs/lakehouse-tables)
  is the page that distinguishes read-only access via Iceberg libraries from
  read/write via the BigQuery Storage API
- [Exporting data: EXPORT TABLE METADATA](https://docs.cloud.google.com/bigquery/docs/exporting-data#export_table_metadata)
  for the statement itself
