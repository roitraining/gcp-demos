import google.auth
import logging
from google.cloud import aiplatform_v1
from google.api_core import exceptions as api_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

creds, project = google.auth.default()
location = "us-central1"


def main():
    client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
    client = aiplatform_v1.EndpointServiceClient(client_options=client_options)

    parent = f"projects/{project}/locations/{location}"

    # List endpoints
    try:
        endpoints = client.list_endpoints(request={"parent": parent})
    except api_exceptions.GoogleAPICallError as e:
        logger.error(f"Failed to list endpoints: {e}")
        return

    any_endpoints = False
    for ep in endpoints:
        any_endpoints = True
        logger.info(
            f"Processing endpoint: name={ep.name}, display_name={ep.display_name}"
        )

        # Undeploy any deployed models from this endpoint
        deployed = getattr(ep, "deployed_models", None) or []
        if deployed:
            for dm in deployed:
                # DeployedModel proto has an 'id' field which is the deployed_model_id
                deployed_model_id = getattr(dm, "id", None) or getattr(
                    dm, "deployed_model_id", None
                )
                if not deployed_model_id:
                    logger.warning(
                        f"Could not determine deployed model id for deployed model: {dm}"
                    )
                    continue

                logger.info(
                    f"Undeploying deployed_model_id={deployed_model_id} from endpoint={ep.name}"
                )
                try:
                    op = client.undeploy_model(
                        request={
                            "endpoint": ep.name,
                            "deployed_model_id": deployed_model_id,
                        }
                    )
                    logger.info("Waiting for undeploy operation to complete...")
                    op.result(timeout=300)
                    logger.info(f"Undeployed {deployed_model_id} from {ep.name}")
                except api_exceptions.GoogleAPICallError as e:
                    logger.error(
                        f"Failed to undeploy model {deployed_model_id} from {ep.name}: {e}"
                    )
                except Exception as e:
                    logger.error(
                        f"Unexpected error undeploying {deployed_model_id} from {ep.name}: {e}"
                    )
        else:
            logger.info("No deployed models found on this endpoint")

        # Delete the endpoint
        logger.info(f"Deleting endpoint: {ep.name}")
        try:
            del_op = client.delete_endpoint(request={"name": ep.name})
            logger.info("Waiting for delete operation to complete...")
            del_op.result(timeout=300)
            logger.info(f"Deleted endpoint {ep.name}")
        except api_exceptions.GoogleAPICallError as e:
            logger.error(f"Failed to delete endpoint {ep.name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error deleting endpoint {ep.name}: {e}")

    if not any_endpoints:
        logger.info("No endpoints found.")


if __name__ == "__main__":
    main()
