import apache_beam as beam

project = 'betterdev-labs'
input_table = 'clouddataflow-readonly:samples.weather_stations'
output_table = 'demos.weather_demo'

def run(argv=None):
  p = beam.Pipeline(argv=[
    '--project=betterdev-labs',
    '--runner=DataflowRunner',
    '--staging_location=gs://betterdev-labs-dataflow/bq_demo_staging',
    '--temp_location=gs://betterdev-labs-dataflow/bq_demo_tmp',
    '--num_workers=20'
    ])

  (p
   | 'read' >> beam.Read(beam.io.BigQuerySource(input_table))
   | 'months with tornadoes' >> beam.FlatMap(
      lambda row: [(int(row['month']), 1)] if row['tornado'] else [])
   | 'monthly count' >> beam.CombinePerKey(sum)
   | 'format' >> beam.Map(lambda (k, v): {'month': k, 'tornado_count': v})
   | 'save' >> beam.Write(
      beam.io.BigQuerySink(
          output_table,
          schema='month:INTEGER, tornado_count:INTEGER',
          create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
          write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE)))
  p.run()

if __name__ == '__main__':
  run()
