# validate_dag.py
# ---------------------------------------------
# Use case: Validates an Airflow DAG file for import errors before deploying to Composer/Airflow.
# How it works: Takes a DAG Python file as a command line argument, attempts to import it using Airflow's DagBag,
# and reports any import errors found. Exits with code 0 if successful, 1 if errors, 2 if no argument provided.
# Setup: Recommended to use Python 3.11 via pyenv. Install Apache Airflow in your environment.
# You'll also need to install any provider modules your DAG uses
# Example setup:
#   pyenv local 3.11
#   uv venv .venv
#   source .venv/bin/activate
#   uv pip install apache-airflow apache-airflow-providers-google
# Usage:
#   uv run validate_dag.py <dag_file.py>

import sys
import os
import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="airflow")
warnings.simplefilter("ignore", DeprecationWarning)

from airflow.models.dagbag import DagBag

# Check for DAG file argument
if len(sys.argv) < 2:
    print("Usage: python validate_dag.py <dag_file.py>")
    sys.exit(2)
DAG_FILE = sys.argv[1]  # DAG file to validate

dag_bag = DagBag(dag_folder=DAG_FILE, include_examples=False)  # Load DAG for validation

errors = dag_bag.import_errors

if errors:
    print("❌ DAG import errors:")
    for f, err in errors.items():
        if DAG_FILE in f:
            print(f"\nFile: {f}\nError:\n{err}")
    sys.exit(1)  # Exit with error code if import errors found
else:
    print("✅ DAG parsed successfully.")
    sys.exit(0)  # Exit with success code
