import logging
import google.auth
from google.cloud import aiplatform, aiplatform_v1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

creds, project = google.auth.default()
location = "us-central1"


def deploy_model_to_endpoint(model_prefix):
    if not project:
        raise RuntimeError(
            "No GCP project found. Set with `gcloud config set project PROJECT`."
        )

    if not model_prefix:
        raise RuntimeError("No model prefix specified.")

    endpoint_display_name = f"{model_prefix}_prediction_endpoint"
    parent = f"projects/{project}/locations/{location}"
    api_endpoint = f"{location}-aiplatform.googleapis.com"

    model_client = aiplatform_v1.ModelServiceClient(
        client_options={"api_endpoint": api_endpoint}
    )

    target_model = None
    for model in model_client.list_models(request={"parent": parent}):
        if model.display_name and model.display_name.startswith(model_prefix):
            target_model = model
            break
    if not target_model:
        raise RuntimeError(
            f"No model found with display_name starting with '{model_prefix}' in {parent}"
        )
    endpoint = aiplatform.Model(model_name=target_model.name).deploy(
        machine_type="n1-standard-4"
    )
    return {"endpoint": endpoint}


if __name__ == "__main__":
    deploy_model_to_endpoint("adopted")
