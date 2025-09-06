import google.auth
import logging

from google.cloud import aiplatform_v1, aiplatform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

creds, project = google.auth.default()
location = "us-central1"


def find_endpoint_and_predict(display_prefix="adopted", location=location):
    if not project:
        logger.error(
            "No gcloud project found. Set with `gcloud config set project PROJECT` or pass project explicitly."
        )
        return

    parent = f"projects/{project}/locations/{location}"

    endpoint_client = aiplatform_v1.EndpointServiceClient(
        client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
    )

    # List endpoints and find first whose display_name starts with the prefix
    endpoints = endpoint_client.list_endpoints(request={"parent": parent})
    target = None
    for ep in endpoints:
        if ep.display_name and ep.display_name.startswith(display_prefix):
            target = aiplatform.Endpoint(endpoint_name=ep.name)
            break

    if not target:
        logger.error(
            f"No endpoint found with display_name starting with '{display_prefix}' in {parent}"
        )
        return

    # Prediction instances for adoption model
    instances = [
        {
            "Type": "Cat",
            "Age": "3",
            "Breed1": "Tabby",
            "Gender": "Male",
            "Color1": "Black",
            "Color2": "White",
            "MaturitySize": "Small",
            "FurLength": "Short",
            "Vaccinated": "No",
            "Sterilized": "No",
            "Health": "Healthy",
            "Fee": "100",
            "PhotoAmt": "2",
        }
    ]

    try:
        prediction = target.predict(instances)
        logger.info(f"Prediction result: {prediction.predictions[0]}")
    except Exception as e:
        logger.error(f"Prediction call failed: {e}")
        raise


if __name__ == "__main__":
    find_endpoint_and_predict()
