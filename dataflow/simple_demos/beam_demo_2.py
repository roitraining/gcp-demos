"""
This file contains minimal, self-contained examples meant to illustrate
several key Apache Beam concepts and transforms. It's intentionally small
and readable so you can experiment locally.

Key points illustrated:
- Creating PCollections from in-memory data with Create
- Grouping keyed data with GroupByKey / CoGroupByKey
- Global and per-key aggregation with CombineGlobally and CombinePerKey

Suggested local setup (macOS):
1. Use pyenv to install a compatible Python (3.11 or earlier is safe for
    most apache-beam releases). Example:
    - pyenv install 3.11.6
    - pyenv local 3.11.6
2. Create and activate a virtual environment (venv):
    - python -m venv .venv
    - source .venv/bin/activate
3. Upgrade pip and install dependencies:
    - pip install --upgrade pip
    - pip install apache-beam
    - If you plan to run on Google Cloud Dataflow, also install:
      pip install apache-beam[gcp]
"""

import apache_beam as beam
from apache_beam.io import WriteToText
import sys

# --- Sample data: city -> zip codes (keyed tuples) ---
city_zip_list = [
    ("Lexington", "40513"),
    ("Nashville", "37027"),
    ("Lexington", "40502"),
    ("Seattle", "98125"),
    ("Mountain View", "94041"),
    ("Seattle", "98133"),
    ("Lexington", "40591"),
    ("Mountain View", "94085"),
]


# --- Sample data: sales amounts (scalar numeric values) ---
sales = [
    1200.50,
    950.00,
    300.75,
    2100.00,
    400.25,
    1800.00,
    500.00,
    700.00,
]

# --- Sample data: sales_rep_id -> sale amounts (keyed tuples) ---
sales_and_reps = [
    ("SP001", 1200.50),
    ("SP002", 950.00),
    ("SP001", 300.75),
    ("SP003", 2100.00),
    ("SP002", 400.25),
    ("SP004", 1800.00),
    ("SP003", 500.00),
    ("SP001", 700.00),
]

# --- Sample data: order numbers and amounts (keyed tuples) ---
order_numbers_amounts = [
    ("ORD1001", 250.00),
    ("ORD1002", 120.50),
    ("ORD1003", 75.25),
    ("ORD1004", 600.00),
    ("ORD1005", 320.10),
    ("ORD1006", 150.75),
    ("ORD1007", 980.00),
    ("ORD1008", 45.00),
]

# --- Sample data: order numbers and delivery dates (keyed tuples) ---
order_numbers_delivery_dates = [
    ("ORD1001", "2025-08-14"),
    ("ORD1002", "2025-08-15"),
    ("ORD1003", "2025-08-16"),
    ("ORD1004", "2025-08-17"),
    ("ORD1005", "2025-08-18"),
    ("ORD1006", "2025-08-19"),
    ("ORD1007", "2025-08-20"),
    ("ORD1008", "2025-08-21"),
]

# --- Build and run the pipeline ---
# Create a Pipeline object. In real projects you typically pass PipelineOptions
# (for runner, project, temp_location, etc.). For this demo we use the default
# direct runner which executes locally.
p = beam.Pipeline()


# Section: create a keyed PCollection and group by key
# What it's doing: creates a PCollection of (city, zip) tuples and groups
# all values by the city key. The result is a PCollection of
# (city, iterable_of_zip_codes).
citycodes = p | "CreateCityCodes" >> beam.Create(city_zip_list)
grouped = citycodes | beam.GroupByKey()
grouped | "write_city_grouped" >> WriteToText("beam_demo_2_city_grouped.txt")


# Section: global aggregation
# What it's doing: create a scalar PCollection and computing the global sum
# across all elements using CombineGlobally. This returns a single-element
# PCollection with the total sales.
sales = p | "CreateSalesCollection" >> beam.Create(sales)
sales_total = sales | beam.CombineGlobally(sum)
sales_total | "write_sales_total" >> WriteToText("beam_demo_2_sales_total.txt")


# Section: per-key aggregation
# What it's doing: create a keyed PCollection (sales_and_reps) and computing
# the sum per salesperson using CombinePerKey. Output is (salesperson, total).
sales = p | "CreateSalesByRepCollection" >> beam.Create(sales_and_reps)
sales_total_by_rep = sales | beam.CombinePerKey(sum)
sales_total_by_rep | "write_sales_total_by_rep" >> WriteToText(
    "beam_demo_2_sales_total_by_rep.txt"
)


# Section: CoGroupByKey (a form of join)
# What it's doing: CoGroupByKey takes a dict of keyed PCollections and produces
# for each key a dictionary-like result with lists of values from each input
# PCollection. This demonstrates how to join related datasets by key.
# Called by: the pipeline and then written to disk for inspection.
orders_amounts = p | "CreateOrderNumbers" >> beam.Create(order_numbers_amounts)
orders_delivery_dates = p | "CreateOrderDeliveryDates" >> beam.Create(
    order_numbers_delivery_dates
)
joined = {
    "orders": orders_amounts,
    "shipping": orders_delivery_dates,
} | beam.CoGroupByKey()
joined | "write_joined_orders_shipping" >> WriteToText(
    "beam_demo_2_joined_orders_shipping.txt"
)

p.run().wait_until_finish()
