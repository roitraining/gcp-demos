# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "dataplex.googleapis.com",
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "dataflow.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "pubsub.googleapis.com"
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Cloud Storage Buckets for Data Zones
resource "google_storage_bucket" "raw_zone" {
  name          = "${var.project_id}-ecommerce-raw-${var.environment}"
  location      = "US" # Multi-region for Dataplex compatibility
  project       = var.project_id
  force_destroy = true

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    zone        = "raw"
    purpose     = "data-ingestion"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_storage_bucket" "curated_zone" {
  name          = "${var.project_id}-ecommerce-curated-${var.environment}"
  location      = "US" # Multi-region for Dataplex compatibility
  project       = var.project_id
  force_destroy = true

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    zone        = "curated"
    purpose     = "processed-data"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_storage_bucket" "quarantine_zone" {
  name          = "${var.project_id}-ecommerce-quarantine-${var.environment}"
  location      = "US" # Multi-region for Dataplex compatibility
  project       = var.project_id
  force_destroy = true

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    zone        = "quarantine"
    purpose     = "failed-quality-checks"
  }

  depends_on = [google_project_service.required_apis]
}

# Create folder structure in raw zone bucket
resource "google_storage_bucket_object" "raw_zone_folders" {
  for_each = toset([
    "web-analytics/",
    "mobile-app/",
    "pos-systems/"
  ])

  name   = each.value
  bucket = google_storage_bucket.raw_zone.name
  source = "/dev/null"
}

# Dataplex Lake
resource "google_dataplex_lake" "ecommerce_lake" {
  name         = "ecommerce-data-lake-${var.environment}"
  location     = var.region
  project      = var.project_id
  display_name = "E-commerce Data Lake (${upper(var.environment)})"
  description  = "Data lake for e-commerce customer analytics pipeline"

  labels = {
    environment = var.environment
    team        = "data-engineering"
  }

  depends_on = [google_project_service.required_apis]
}

# Raw Data Zone
resource "google_dataplex_zone" "raw_zone" {
  name         = "raw-zone"
  location     = var.region
  project      = var.project_id
  lake         = google_dataplex_lake.ecommerce_lake.name
  display_name = "Raw Data Zone"
  description  = "Zone for ingested raw data from multiple sources"

  type = "RAW"

  discovery_spec {
    enabled  = true
    schedule = "0 */4 * * *" # Every 4 hours

    include_patterns = [
      "gs://${google_storage_bucket.raw_zone.name}/**"
    ]
  }

  resource_spec {
    location_type = "MULTI_REGION"
  }

  labels = {
    environment = var.environment
    data-tier   = "raw"
  }
}

# Curated Data Zone
resource "google_dataplex_zone" "curated_zone" {
  name         = "curated-zone"
  location     = var.region
  project      = var.project_id
  lake         = google_dataplex_lake.ecommerce_lake.name
  display_name = "Curated Data Zone"
  description  = "Zone for processed, quality-assured data"

  type = "CURATED"

  discovery_spec {
    enabled  = true
    schedule = "0 6 * * *" # Daily at 6 AM

    include_patterns = [
      "gs://${google_storage_bucket.curated_zone.name}/**"
    ]
  }

  resource_spec {
    location_type = "MULTI_REGION"
  }

  labels = {
    environment = var.environment
    data-tier   = "curated"
  }
}

# Raw Zone Asset (single asset for the entire raw bucket)
resource "google_dataplex_asset" "raw_data" {
  name          = "raw-data-asset"
  location      = var.region
  project       = var.project_id
  lake          = google_dataplex_lake.ecommerce_lake.name
  dataplex_zone = google_dataplex_zone.raw_zone.name
  display_name  = "Raw Data Storage"
  description   = "Raw data from all sources: web analytics, mobile app, and POS systems"

  resource_spec {
    name = "projects/${var.project_id}/buckets/${google_storage_bucket.raw_zone.name}"
    type = "STORAGE_BUCKET"
  }

  discovery_spec {
    enabled  = true
    schedule = "0 */2 * * *" # Every 2 hours

    # Include patterns to focus discovery on specific folders
    include_patterns = [
      "gs://${google_storage_bucket.raw_zone.name}/web-analytics/**",
      "gs://${google_storage_bucket.raw_zone.name}/mobile-app/**",
      "gs://${google_storage_bucket.raw_zone.name}/pos-systems/**"
    ]

    # Exclude temporary or processing files
    exclude_patterns = [
      "gs://${google_storage_bucket.raw_zone.name}/**/temp/**",
      "gs://${google_storage_bucket.raw_zone.name}/**/_processing/**"
    ]
  }

  labels = {
    zone        = "raw"
    environment = var.environment
    sources     = "web-mobile-pos"
  }
}

# Curated Zone Asset
resource "google_dataplex_asset" "curated_data" {
  name          = "curated-data-asset"
  location      = var.region
  project       = var.project_id
  lake          = google_dataplex_lake.ecommerce_lake.name
  dataplex_zone = google_dataplex_zone.curated_zone.name
  display_name  = "Curated Data Storage"
  description   = "Processed and quality-assured data ready for analytics"

  resource_spec {
    name = "projects/${var.project_id}/buckets/${google_storage_bucket.curated_zone.name}"
    type = "STORAGE_BUCKET"
  }

  discovery_spec {
    enabled  = true
    schedule = "0 6 * * *" # Daily at 6 AM
  }

  labels = {
    zone        = "curated"
    environment = var.environment
    quality     = "verified"
  }
}

# Data Quality Scan for automated profiling
resource "google_dataplex_datascan" "data_quality_scan" {
  data_scan_id = "ecommerce-data-quality-scan"
  location     = var.region
  project      = var.project_id
  display_name = "E-commerce Data Quality Scan"
  description  = "Automated data quality scanning and profiling"

  data {
    resource = google_dataplex_asset.raw_data.name
  }

  execution_spec {
    trigger {
      schedule {
        cron = "0 */4 * * *" # Every 4 hours
      }
    }
  }

  # Data profiling configuration
  data_profile_spec {
    sampling_percent = 100.0

    # Include specific fields for profiling
    include_fields {
      field_names = ["*"] # Profile all fields
    }
  }

  labels = {
    environment = var.environment
    scan-type   = "data-profile"
  }
}

# Data Quality Rules Scan
resource "google_dataplex_datascan" "data_quality_rules" {
  data_scan_id = "ecommerce-quality-rules-scan"
  location     = var.region
  project      = var.project_id
  display_name = "E-commerce Data Quality Rules"
  description  = "Business rule validation for e-commerce data"

  data {
    resource = google_dataplex_asset.raw_data.name
  }

  execution_spec {
    trigger {
      schedule {
        cron = "0 */4 * * *" # Every 4 hours
      }
    }
  }

  # Data quality rules
  data_quality_spec {
    sampling_percent = 100.0

    # Rule: Check for null values in critical fields
    rules {
      column    = "user_id"
      dimension = "COMPLETENESS"
      threshold = 0.7 # Allow 30% nulls (anonymous users)

      non_null_expectation {}
    }

    # Rule: Validate email format if present
    rules {
      column    = "email"
      dimension = "VALIDITY"
      threshold = 0.95

      regex_expectation {
        regex = "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      }
    }

    # Rule: Check timestamp format
    rules {
      column    = "timestamp"
      dimension = "VALIDITY"
      threshold = 1.0

      non_null_expectation {}
    }

    # Rule: Validate transaction amounts are positive
    rules {
      column    = "price"
      dimension = "VALIDITY"
      threshold = 0.99

      range_expectation {
        min_value = "0"
        max_value = "10000"
      }
    }
  }

  labels = {
    environment = var.environment
    scan-type   = "data-quality"
  }
}

# Service Account for Dataplex operations
resource "google_service_account" "dataplex_sa" {
  account_id   = "dataplex-service-${var.environment}"
  display_name = "Dataplex Service Account"
  description  = "Service account for Dataplex operations and data profiling"
  project      = var.project_id
}

# IAM bindings for Dataplex service account
resource "google_project_iam_member" "dataplex_sa_roles" {
  for_each = toset([
    "roles/dataplex.developer",
    "roles/dataplex.dataReader",
    "roles/dataplex.dataWriter",
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/dataproc.worker",
    "roles/dataproc.editor"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.dataplex_sa.email}"
}

# Pub/Sub topic for data quality notifications
resource "google_pubsub_topic" "data_quality_alerts" {
  name    = "data-quality-alerts-${var.environment}"
  project = var.project_id

  labels = {
    environment = var.environment
    purpose     = "data-quality"
  }

  depends_on = [google_project_service.required_apis]
}

# BigQuery dataset for processed data
resource "google_bigquery_dataset" "ecommerce_analytics" {
  dataset_id  = "ecommerce_analytics_${var.environment}"
  project     = var.project_id
  location    = var.region
  description = "Analytics dataset for e-commerce customer data"

  labels = {
    environment = var.environment
    team        = "analytics"
  }

  depends_on = [google_project_service.required_apis]
}

# Outputs
output "lake_name" {
  description = "Name of the Dataplex lake"
  value       = google_dataplex_lake.ecommerce_lake.name
}

output "raw_bucket_name" {
  description = "Name of the raw data bucket"
  value       = google_storage_bucket.raw_zone.name
}

output "curated_bucket_name" {
  description = "Name of the curated data bucket"
  value       = google_storage_bucket.curated_zone.name
}

output "quarantine_bucket_name" {
  description = "Name of the quarantine bucket"
  value       = google_storage_bucket.quarantine_zone.name
}

output "dataplex_service_account" {
  description = "Email of the Dataplex service account"
  value       = google_service_account.dataplex_sa.email
}

output "pubsub_topic" {
  description = "Pub/Sub topic for data quality alerts"
  value       = google_pubsub_topic.data_quality_alerts.name
}
