# What's new — 2026 update

> [!NOTE]
> Updated August 1, 2026. For the previous update, see
> [What's new — 2025](whats-new-2025.md).

The theme this year is **query performance** and **AI**. The BigQuery additions
are built around reading an execution plan and seeing why a query is slow, and
there is a new `ai/` area covering AutoML, Vertex AI Pipelines, and the Agent
Development Kit.

## AI

1. **ADK callback examples** (`ai/adk/adk_callback_examples.py`) — one small,
   self-contained scenario per callback type, with a cheat sheet for what each
   return value does. Verified against `google-adk` 2.5.0; runnable all at once
   or one demo at a time.
2. **ADK + BigQuery MCP agent** (`ai/adk/mcp_sa_demo/`) — an agent that reaches
   BigQuery through its MCP endpoint, showing how to attach Application Default
   Credentials as MCP request headers and refresh the token only when it expires.
3. **AutoML forecasting demo** (`ai/automl/`) — liquor sales forecasting on
   tabular data, end to end: dataset, training job, batch prediction, and a
   Looker Studio dashboard. The README documents the timing traps (≈2 hours to
   train, ≈30 minutes to predict) and how to pre-run it before class.
4. **AutoML adoption demo** (`ai/automl/adoption_deploy.py`,
   `adoption_predict.py`) — deploy and predict scripts for the adoption model.
5. **Vertex AI Pipelines demo** (`ai/pipelines/`) — instructor notes for
   presenting a simple pipeline: the definition, the graph, the created dataset
   and endpoint, and the teardown.
6. **Endpoint cleanup helper** (`ai/del_endpoints.py`) — undeploys models and
   deletes endpoints left behind by the AI demos.

## Model Armor (GSP1327)

7. **Model Armor notebooks** (`GSP1327/`) — screening LLM prompts and responses
   for security and safety risks. Three notebooks: a base walkthrough via REST,
   an extended version, and one covering **project floor settings** with the
   `google-cloud-modelarmor` Python SDK.

## BigQuery — query performance

These are the backing examples for the performance Do-It-Nows. Several are meant
to be **pasted into the editor and read in the query validator, not run** — the
select-star example in particular would cost more than $15 on demand. Each file
says so at the top.

8. **Execution details** (`execution_details_example.sql`) — a deliberately
   heavyweight join-and-aggregate for reading the execution graph.
9. **Join types** (`join_types_example.sql`) — broadcast versus hash join, and
   why a 10,000-row dimension table changes the plan.
10. **Shuffle and spill** (`shuffle_spill_example.sql`) — contrasts a query where
    no rows need to move with one that forces a shuffle.
11. **Aggregate first** (`aggregate_first_example.sql`) — the same question
    answered before and after pushing the aggregation below the join.
12. **Partition pruning** (`pruning_example.sql`) — the same filter against an
    unpartitioned and a partitioned table, compared by bytes read.
13. **`SELECT *` cost** (`select_star_example.sql`) — ~2.4 TB versus ~13 GB for
    two columns, on a public dataset.
14. **Join constraints** (`constraints_example.sql`) — a join that cannot change
    the answer, and what declaring constraints lets the optimizer do about it.
15. **Query insights** (`insights_example.sql`) — a fan-out join that silently
    inflates a revenue total 1,000×. Generates its own data, so it bills 0 bytes.

## BigQuery — loading data

16. **Schema autodetect** (`autodetect_demo.sh`) — generates two CSV drops where
    the vendor writes `N/A` in a numeric column, positioned so autodetect
    succeeds on the small file and fails on the large one. Paste into Cloud Shell.
17. **`LOAD DATA`** (`load_data_example.sql`) — the same load job the console and
    `bq load` produce, expressed in SQL with a pinned schema.
18. **Storage Write API** (`storage_write_example.js`) — streaming rows with the
    default stream and a `JSONWriter` built from the table's own schema.
19. **Information schema** (`information_schema_examples.sql`) — extended with
    additional metadata queries.

## Lakehouse — Iceberg on BigQuery

20. **Iceberg tutorial** (`lakehouse/`) — a walkthrough of the three different
    things BigQuery calls "Iceberg" (managed, Lakehouse catalog, and external)
    and how they differ in the one way that matters: who owns the table
    metadata. You create one of each, write from both BigQuery and Spark, and
    watch which writes are accepted. Includes setup and teardown scripts, the
    full SQL, and a BigQuery Studio notebook for the Spark half.

> [!WARNING]
> **Under construction — check before using with an audience.** Parts of the
> tutorial have been run end to end, but several sections have not, and
> `iceberg_teardown.sh` has a known bug that can report success without
> deleting anything. The `lakehouse/README.md` **Status** section lists exactly
> what is verified and what is not; read it first.

## Dataplex

21. **Lineage tools** (`dataplex/lineage/lineage_tools.py`) — lists lineage
    processes and their events through the Data Lineage API.

## Do It Nows

22. **New and revised activities** — a substantial batch of new Do-It-Nows,
    mostly covering the BigQuery performance and loading material above, plus a
    restyled activity site (`docs/custom.css`).

## Housekeeping

23. Dependency updates across `dlp-demo/` and `utilities/shopping_list_api/`.
24. Top-level `requirements.txt` added.

## Works in Progress

- Finishing the Iceberg tutorial: verifying the unverified sections and fixing
  the teardown script's false-success bug
- Filling in the AutoML adoption demo write-up and the `GSP1327/` README
- Finishing custom log-sink -> pub/sub -> cloud function -> interesting action
  demo (carried over from 2025)
