# 🚀 ROI GCP Training Demos

Welcome to a collection of Google Cloud Platform demonstrations and hands-on examples brought to you by ROI Training! This repository contains demos designed to illustrate key GCP concepts, best practices, and common use cases across various Google Cloud services.

Whether you're an instructor leading a training session or a student exploring GCP capabilities, these demos provide hands-on experience with the most important Google Cloud services and patterns.

> [!NOTE]
> **Returning after a while?** Each year's additions are summarized separately:
> **[What's new — 2026](whats-new-2026.md)** (AI, BigQuery query
> performance, Iceberg) and **[What's new — 2025](whats-new-2025.md)**.

## 1. Quick Start

Get started in just a few steps:

```bash
# Clone the repository
cd ~
git clone https://github.com/roitraining/gcp-demos.git
cd gcp-demos

# Set your project (replace with your actual project ID)
export GOOGLE_CLOUD_PROJECT=your-project-id
gcloud config set project $GOOGLE_CLOUD_PROJECT
```

---

## 2. BigQuery

*Explore the power of Google's serverless data warehouse*

#### 🔍 **SQL Examples Collection**
The `bigquery/` directory contains a comprehensive set of SQL examples demonstrating:
- **Array Functions**: Complex array manipulations and searching (`arrays_examples.sql`)
- **Approximate Functions**: Using approximate functions for large-scale analytics (`approx_example.sql`)
- **ELT Patterns**: Extract, Load, Transform patterns (`elt_examples.sql`)
- **External Data**: Working with Hive-style external tables (`external_hive_example.sql`)
- **Information Schema**: Metadata queries and system introspection (`information_schema_examples.sql`)
- **Materialized Views**: Performance optimization with precomputed results (`mv_example.sql`)
- **Time Travel**: Querying historical data snapshots (`time_travel_example.sql`)
- **User-Defined Functions**: Custom SQL and JavaScript functions (`udf_examples.sql`)
- **Views**: Creating and managing logical views (`views_example.sql`)

#### ⚡ **Query Performance Examples**
Backing examples for the performance activities — each one pairs a slow query with a faster query answering the same question:
- **Execution Details**: Reading the execution graph (`execution_details_example.sql`)
- **Join Types**: Broadcast vs. hash joins (`join_types_example.sql`)
- **Shuffle & Spill**: When rows have to move between workers (`shuffle_spill_example.sql`)
- **Aggregate First**: Pushing aggregation below a join (`aggregate_first_example.sql`)
- **Partition Pruning**: Bytes read with and without partitioning (`pruning_example.sql`)
- **`SELECT *` Cost**: ~2.4 TB vs. ~13 GB for two columns (`select_star_example.sql`)
- **Constraints**: Letting the optimizer drop a join that can't change the answer (`constraints_example.sql`)
- **Query Insights**: A fan-out join that inflates a total 1,000× (`insights_example.sql`)

> [!CAUTION]
> Several of these are meant to be **pasted into the editor and read in the query validator, not run** — the `SELECT *` example would cost more than $15 on demand. Each file states this at the top.

#### 📥 **Loading Data**
- **Schema Autodetect**: Generates CSV drops where autodetect succeeds on one file and fails on another (`autodetect_demo.sh`)
- **`LOAD DATA`**: Load jobs expressed in SQL with a pinned schema (`load_data_example.sql`)
- **Storage Write API**: Streaming rows via the default stream (`storage_write_example.js`)

#### 🏗️ **Schema Design Demo**
The `bigquery/schema-demo/` directory provides a complete demonstration of schema design impact:
- Compare normalized vs. denormalized table performance
- Explore nested and repeated fields
- Understand partitioning and clustering benefits
- Generate sample datasets for testing

#### 📚 **Interactive Do-It-Nows**
Access 20+ hands-on BigQuery activities at: **https://roitraining.github.io/gcp-demos/#0**

These self-paced exercises cover everything from basic queries to advanced analytics patterns.

---

## 3. AI & Machine Learning

*Vertex AI, AutoML, and agent development*

#### 🤖 **Agent Development Kit (ADK)**
The `ai/adk/` directory contains:
- **Callback Examples** (`adk_callback_examples.py`): One self-contained scenario per callback type, with a cheat sheet for what each return value does
- **BigQuery MCP Agent** (`mcp_sa_demo/`): An agent reaching BigQuery over MCP, showing how to attach Application Default Credentials as request headers

#### 📊 **AutoML**
The `ai/automl/` directory demonstrates:
- **Forecasting**: Liquor sales forecasting on tabular data — dataset, training, batch prediction, and a Looker Studio dashboard
- **Adoption**: Model deploy and predict scripts

> [!IMPORTANT]
> Training runs ≈2 hours and batch prediction ≈30 minutes, so these are not feasible to run live. See `ai/automl/README.md` for how to pre-run them before class.

#### 🔗 **Vertex AI Pipelines**
The `ai/pipelines/` directory holds instructor notes for presenting a simple pipeline: the definition, the graph, the created dataset and endpoint, and teardown.

#### 🧹 **Cleanup**
`ai/del_endpoints.py` undeploys models and deletes endpoints left behind by the AI demos.

---

## 4. Model Armor

#### 🛡️ **Prompt & Response Screening**
The `GSP1327/` directory contains notebooks demonstrating how Model Armor screens LLM prompts and responses for security and safety risks:
- Base walkthrough using REST API calls
- Extended scenarios
- **Floor settings**: Establishing a minimum enforcement bar at the org, folder, or project level using the `google-cloud-modelarmor` Python SDK

---

## 5. Lakehouse (Iceberg)

#### 🧊 **Iceberg on BigQuery**
The `lakehouse/` directory walks through the three different things BigQuery calls "Iceberg" — **managed**, **Lakehouse catalog**, and **external** — and how they differ in the one way that matters: who owns the table metadata. You create one of each, write from both BigQuery and Spark, and watch which writes are accepted and which are refused.

Includes setup/teardown scripts, the full SQL, and a BigQuery Studio notebook for the Spark half.

> [!WARNING]
> **Under construction.** Parts have been run end to end, but several sections have not, and the teardown script has a known bug that can report success without deleting anything. Read the **Status** section of `lakehouse/README.md` before using this with an audience.

---

## 6. Composer (Apache Airflow)

#### 🛠️ **DAG Development**
The `composer/dag_development/` directory contains DAG validation tools and scripts

#### 📋 **Example DAGs**
The `composer/dags/` directory includes simple but useful DAG examples

---

## 7. Dataflow

#### 🔄 **Streaming Pipeline Demo**
The `dataflow/dflow-bq-stream-python/` directory contains a complete streaming example:
- Pub/Sub to BigQuery streaming pipeline
- Window functions and aggregations
- Nested/repeated data handling
- Local and cloud execution patterns

#### 🧪 **Simple Beam Examples**
The `dataflow/simple_demos/` directory provides:
- Basic Apache Beam concepts
- Transform examples
- Pipeline patterns and best practices

---

## 8. Data Loss Prevention (DLP)

#### 🌐 **Interactive DLP Demo**
Experience DLP capabilities firsthand: **https://bit.ly/roi-dlp-demo**

1. Enter text with various data types in the left pane
2. Watch DLP identify and classify sensitive information
3. Experiment with different remediation strategies
4. Explore contextual confidence ratings

#### 💻 **Source Code**
The `dlp-demo/` directory contains the complete application source:
- Cloud Run deployment configuration
- Python Flask application
- DLP API integration examples
- Docker containerization setup

---

## 9. Dataproc

#### 📈 **Scaling Demonstrations**
- **Manual Scaling**: Traditional cluster resizing (`dataproc_scale_demo.sh`)
- **Autoscaling**: Dynamic resource allocation (`dataproc_autoscale_demo.sh`)

---

## 10. Dataform

https://github.com/jwdavis/dataform-demo

---

## 11. Dataplex

#### 📊 **Data Profiling**
The `dataplex/profiling/` directory demonstrates:
- Automated data quality assessment

#### 🔗 **Data Lineage**
The `dataplex/lineage/` directory contains tools for listing lineage processes and their events via the Data Lineage API

---

## 12. Cloud Functions

Examples include:
- Sample function for processing log entries received via Pub/Sub

---

## 13. Security & IAM

#### 🔑 **Authentication Examples**
The `security/` directory contains:
- Service account authentication patterns
- OAuth and API key management
- Organization policy examples and constraints

---

## 14. Terraform

The `terraform/` directory contains:
- **Resource Export** (`exp_to_tf.sh`): Exports a project's resources as Terraform HCL

---

## 15. Utilities

The `utilities/` directory contains:
- **Shopping List API** (`shopping_list_api/`): A small web service that generates Costco shopping lists and returns them as JSON — useful as a demo data source

---

## 🚀 16. Coming Soon...

The following areas are under active development:

- **Pub/Sub**: Messaging and event streaming examples
- **Iceberg**: Finishing verification of the `lakehouse/` tutorial
- **Log sink → Pub/Sub → Cloud Function**: End-to-end event-driven demo

---

## 📋 Quick Reference

| Service     | Directory    | Key Features                                   |
| ----------- | ------------ | ---------------------------------------------- |
| BigQuery    | `bigquery/`  | SQL examples, query performance, schema design  |
| AI / ML     | `ai/`        | ADK agents, AutoML, Vertex AI Pipelines        |
| Model Armor | `GSP1327/`   | LLM prompt/response screening, floor settings  |
| Lakehouse   | `lakehouse/` | Iceberg tables on BigQuery and Spark           |
| Composer    | `composer/`  | Airflow DAGs, workflow orchestration           |
| Dataflow    | `dataflow/`  | Streaming pipelines, Apache Beam               |
| DLP         | `dlp-demo/`  | Data classification, sensitive data protection |
| Dataproc    | `dataproc/`  | Spark/Hadoop clusters, scaling demos           |
| Dataplex    | `dataplex/`  | Data profiling, lineage                        |
| Security    | `security/`  | IAM, authentication, policies                  |

Happy learning! 🎓
