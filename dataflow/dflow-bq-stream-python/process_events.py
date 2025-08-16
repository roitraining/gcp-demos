import os
import apache_beam as beam
import apache_beam.transforms.window as window
import random
import argparse
import json
import schema_defs

from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.transforms import window
from datetime import datetime

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# takes input element, and returns an array of one bq row
# that includes the window end time
class CreateBQRow(beam.DoFn):
  def process(self, element, window=beam.DoFn.WindowParam):
    window_end_ts = window.end.to_utc_datetime().isoformat()
    row = {"window_ending": window_end_ts,
        "pos_id": element[0],
        "transactions": element[1]
    }
    # print(f"Writing row:{row}")
    return [row]

# convert message into a kv pair
# with transaction info in an objet
def make_kv(element):
    kv = (
        element["pos_id"], 
        {
            "ts": element["ts"],
            "zip": element["zip"],
            "sale_amount": element["sale_amount"]
        }
    )
    return kv

parser = argparse.ArgumentParser()
parser.add_argument(
    "--dataset_id",
    default='dflow_demo')
parser.add_argument(
    "--table_id",
    default='messages')
parser.add_argument(
    "--sub_id",
    default='demo_sub')
parser.add_argument(
    "--window_size",
    default=10)

known_args, pipeline_args = parser.parse_known_args()

# check to see if user specified --project; quit if not
pipeline_args_dict = {}
for index in range(1, len(pipeline_args), 2):
    pipeline_args_dict[pipeline_args[index-1].replace("--", "", 1)] = pipeline_args[index]

if not ("project" in pipeline_args_dict):
    print("project argument is missing")
    quit()

sub_path = f"projects/{pipeline_args_dict['project']}/subscriptions/{known_args.sub_id}"

# check to see if dataset exists, create if not
bq_client = bigquery.Client()
dataset_path = f"{pipeline_args_dict['project']}.{known_args.dataset_id}"
try:
    dataset = bq_client.get_dataset(dataset_path)
except NotFound:
    dataset = bigquery.Dataset(dataset_path)
    dataset.location = "US"
    dataset = bq_client.create_dataset(dataset, timeout=30)

# check to see if messages table exists, create if not
messages_table_path = f"{pipeline_args_dict['project']}.{known_args.dataset_id}.{known_args.table_id}"
try:
    table = bq_client.get_table(messages_table_path)
except NotFound:
    table_ref = dataset.table(known_args.table_id)
    table = bigquery.Table(table_ref, schema=schema_defs.ccl_messages_schema)
    table = bq_client.create_table(table)

# check to see if nested table exists, create if not
nested_table_path = f"{pipeline_args_dict['project']}.{known_args.dataset_id}.{known_args.table_id}_nested"
try:
    table = bq_client.get_table(nested_table_path)
except NotFound:
    table_ref = dataset.table(f"{known_args.table_id}_nested")
    table = bigquery.Table(table_ref, schema=schema_defs.ccl_messages_nested_schema)
    table = bq_client.create_table(table)

pipeline_options = PipelineOptions(pipeline_args)
pipeline_options.view_as(SetupOptions).save_main_session = False
pipeline_options.view_as(StandardOptions).streaming = True

p = beam.Pipeline(options=pipeline_options)
messages = p | "read messages" >> beam.io.ReadFromPubSub(subscription = sub_path)
decoded_messages = messages | "decode bytes" >> beam.Map(lambda x: x.decode('utf-8'))
json_messages = decoded_messages | "convert to json" >> beam.Map(lambda x: json.loads(x))

# write the transactions as is into messages table
json_messages | "write messages to BQ" >> beam.io.WriteToBigQuery(
    messages_table_path.replace(".", ":", 1),
    schema=schema_defs.beam_messages_schema,
    write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
    create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
)

# convert rows into kv pairs, window them, group them, create BQ Row
pos_sale_kvs = json_messages | "create key/value pairs" >> beam.Map(make_kv)
windowed_kvs = pos_sale_kvs | "window elements" >> beam.WindowInto(window.FixedWindows(10))
nested_rows = windowed_kvs | "group per key/window" >> beam.GroupByKey()
nested_labelled_rows = nested_rows | "create BQ nested row" >> beam.ParDo(CreateBQRow())

# then stream rows into BQ nested table 
nested_labelled_rows | "write nested rows to BQ" >> beam.io.WriteToBigQuery(
    nested_table_path.replace(".", ":", 1),
    schema=schema_defs.beam_messages_nested_schema,
    write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
    create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
)

if "DataflowRunner" in pipeline_args:
    p.run()
else:
    p.run().wait_until_finish()