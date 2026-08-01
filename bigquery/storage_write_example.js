// Streams rows into class.live_usage with the BigQuery Storage Write API,
// using the simplest arrangement the API offers: JSON rows appended to the
// table's default stream.
//
// The JSONWriter converts each JSON row to the protocol-buffer format the
// API requires, using a descriptor built from the table's own schema.
// TIMESTAMP columns are passed as microseconds since the epoch.
//
// Run in Cloud Shell (see the Do-It-Now for setup):
//   node storage_write_example.js

const {adapt, managedwriter} = require('@google-cloud/bigquery-storage');
const {WriterClient, JSONWriter} = managedwriter;

const projectId =
  process.env.GOOGLE_CLOUD_PROJECT || process.env.DEVSHELL_PROJECT_ID;
const datasetId = 'class';
const tableId = 'live_usage';

const ROWS_TO_SEND = 30;

async function main() {
  const destinationTable = `projects/${projectId}/datasets/${datasetId}/tables/${tableId}`;
  const writeClient = new WriterClient({projectId});
  try {
    // Fetch the table's schema and turn it into a proto descriptor
    const writeStream = await writeClient.getWriteStream({
      streamId: `${destinationTable}/streams/_default`,
      view: 'FULL',
    });
    const protoDescriptor = adapt.convertStorageSchemaToProto2Descriptor(
      writeStream.tableSchema,
      'root'
    );

    // Open a connection to the table's default stream
    const connection = await writeClient.createStreamConnection({
      streamId: managedwriter.DefaultStream,
      destinationTable,
    });
    const writer = new JSONWriter({connection, protoDescriptor});

    // Append one row per second, as if events were arriving live
    for (let i = 1; i <= ROWS_TO_SEND; i++) {
      const row = {
        meeting_id: `m-live-${String(i).padStart(3, '0')}`,
        user_id: `u-${String(i % 5).padStart(4, '0')}`,
        minutes: ((i * 7) % 60) + 1,
        event_ts: Date.now() * 1000,
      };
      const result = await writer.appendRows([row]).getResult();
      const err = result.error || (result.rowErrors || []).length;
      console.log(`row ${i}/${ROWS_TO_SEND}: ${err ? JSON.stringify(result) : 'appended'}`);
      await new Promise((r) => setTimeout(r, 1000));
    }
    writer.close();
  } finally {
    writeClient.close();
  }
}

main().catch(console.error);
