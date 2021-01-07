# Dataflow Python Streaming Demo

## Purpose

On the surface, this is a very simple demo intended to show Dataflow streaming
using the Python SDK.

There are a few fun little tricks and techniques invovled, including:

* Checking for topic/sub existence
* Encoding objects into messages
* Reading the end time of BEAM windows
* Checking for dataset/table existence in BQ
* Streaming nested/repeated data into BQ

## Setup

Setup will do the following:

* Create and activate a python virtual environment
* Install dependencies for both pieces of the demo code
* Create a service account and make it an editor
* Create and download a key file for the service account
* Set an environment variable that will point the code to the service account keyfile
* Create a bucket that is used by the dataflow job
* Enable the BQ, PubSub, and Dataflow services

1. Clone the repo, and change directories to `dflow-bq-stream-python`:

    ```bash
    git clone https://github.com/roitraining/gcp-demos.git
    cd gcp-demos/dflow-bq-stream-python
    ```

2. Make sure that **gcloud** is configured to point to the project you want to work in.

3. Run the `setup.sh` script providing the name of the service account you want the demo code to use:

    ```bash
    . ./setup.sh demo-sa
    ```

## Starting the pipeline

This section creates a Dataflow job which reads the messages from a PubSub
subscription, writes all messages into a `messages` table, and also windows the
messages and writes nested/repeated rows for each window into a
`messages_nested` table.

1. Make sure that you are in the **dflow-bq-stream-python** directory
2. Deploy the Dataflow job like this:

   ```bash
   python3 process_events.py \
   --runner DataflowRunner \
   --region us-central1 \
   --project $PROJECT_ID \
   --staging_location gs://$PROJECT_ID-dflow-demo/ \
   --temp_location gs://$PROJECT_ID-dflow-demo/
   ```

3. If you want to adjust the fixed window size from 10 seconds, you can provide
   an optioanl command-line argument `--window-size` (defined in seconds).

4. If you want to run the pipeline locally, the command looks like this:

   ```bash
   python3 process_events.py \
   -- project $PROJECT_ID
   ```

## Sending events

This part of this demo sends a stream of events to a Pub/Sub topic,
one per second.

1. If the pipeline is running in Dataflow, run the `send_events` script:

    ```bash
    python3 send_events.py \
        --project_id=$PROJECT_ID
    ```

    You may optionally change the topic and sucscription names if you like by
    specifying additional arguments: `topic_id` and `sub_id`.

2. If you are running the pipeline locally, you will need to open a 2nd
   terminal window and start the sending utility.

   Assuming you cloned the repo into your home directory, enter the following
   into the 2nd terminal window:

   ```bash
    cd gcp-demos/dflow-demo
    source env/bin/activate
    python3 send_events.py \
        --project_id=$PROJECT_ID
   ```

## Checking out results

1. Check out the pipeline in Dataflow (if running there)
   1. Note the branch and two different sinks
   2. Note that windowing happens after several transforms
   3. Note the aggregation

1. Check out the messages table in BQ and see all the individual messages
1. Check out the messages_nested table in BQ and see the nested data