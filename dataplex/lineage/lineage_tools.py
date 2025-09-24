from google.cloud import datacatalog_lineage_v1
from datetime import datetime, timezone, timedelta


def list_processes():
    # Create a client
    client = datacatalog_lineage_v1.LineageClient()

    # Initialize request argument(s)
    request = datacatalog_lineage_v1.ListProcessesRequest(
        parent=parent,
    )

    # Make the request
    page_result = client.list_processes(request=request)

    # Handle the response
    for response in page_result:
        yield response


def list_lineage_events(event_name):
    # Create a client
    client = datacatalog_lineage_v1.LineageClient()

    # Initialize request argument(s)
    request = datacatalog_lineage_v1.ListLineageEventsRequest(
        parent=event_name,
    )

    # Make the request
    page_result = client.list_lineage_events(request=request)

    # Handle the response
    for response in page_result:
        yield response


def list_runs(process_name, num_days):

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now_utc + timedelta(days=-num_days)

    # Create a client
    client = datacatalog_lineage_v1.LineageClient()

    # Initialize request argument(s)
    request = datacatalog_lineage_v1.ListRunsRequest(
        parent=process_name,
    )

    # Make the request
    page_result = client.list_runs(request=request)

    # Handle the response
    for response in page_result:
        dt = datetime.fromtimestamp(response.start_time.timestamp())
        if dt >= cutoff:
            yield response


if __name__ == "__main__":
    parent = "projects/jwd-gcp-demos/locations/us"
    processes = list_processes()
    for process in processes:
        print(process)
        print(f"Runs for {process.name}:")
        runs = list_runs(process_name=process.name, num_days=1)
        for run in runs:
            print("Run start time:", run.start_time)
            print(run)
            print(f"Events for {run.name}:")
            events = list_lineage_events(run.name)
            for event in events:
                print(f"  {event}")
