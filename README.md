# 🚀 ROI GCP Training Demos

Welcome to a collection of Google Cloud Platform demonstrations and hands-on examples brought to you by ROI Training! This repository contains demos designed to illustrate key GCP concepts, best practices, and common use cases across various Google Cloud services.

Whether you're an instructor leading a training session or a student exploring GCP capabilities, these demos provide hands-on experience with the most important Google Cloud services and patterns.

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

## 3. Composer (Apache Airflow)

#### 🛠️ **DAG Development**
The `composer/dag_development/` directory contains DAG validation tools and scripts

#### 📋 **Example DAGs**
The `composer/dags/` directory includes simple but useful DAG examples

---

## 4. Dataflow

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

## 5. Data Loss Prevention (DLP)

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

## 6. Dataproc

#### 📈 **Scaling Demonstrations**
- **Manual Scaling**: Traditional cluster resizing (`dataproc_scale_demo.sh`)
- **Autoscaling**: Dynamic resource allocation (`dataproc_autoscale_demo.sh`)

---

## 7. Dataform

https://github.com/jwdavis/dataform-demo

---

## 8. Dataplex

#### 📊 **Data Profiling**
The `dataplex/profiling/` directory demonstrates:
- Automated data quality assessment

---

## 9. Cloud Functions

Examples include:
- Sample function for processing log entries received via Pub/Sub

---

## 10. Security & IAM

#### 🔑 **Authentication Examples**
The `security/` directory contains:
- Service account authentication patterns
- OAuth and API key management
- Organization policy examples and constraints

---

## 🚀 11. Coming Soon...

The following areas are under active development:

- **Pub/Sub**: Messaging and event streaming examples
- **Terraform**: Infrastructure as Code templates
- **Utilities**: Helper scripts and tools

---

## 📋 Quick Reference

| Service  | Directory   | Key Features                                   |
| -------- | ----------- | ---------------------------------------------- |
| BigQuery | `bigquery/` | SQL examples, schema design, analytics         |
| Composer | `composer/` | Airflow DAGs, workflow orchestration           |
| Dataflow | `dataflow/` | Streaming pipelines, Apache Beam               |
| DLP      | `dlp-demo/` | Data classification, sensitive data protection |
| Dataproc | `dataproc/` | Spark/Hadoop clusters, scaling demos           |
| Security | `security/` | IAM, authentication, policies                  |

Happy learning! 🎓
