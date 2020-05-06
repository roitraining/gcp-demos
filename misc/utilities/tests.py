# from models.models import PollingRecord
# from utilities import airtable
import google.cloud.dlp

def deid(args):
    dlp = google.cloud.dlp_v2.DlpServiceClient()
    parent = dlp.project_path('roi-gcp-demos')
    inspect_config = {
        "info_types": [{"name": "EMAIL_ADDRESS"}]
    }
    deidentify_config = {
        "info_type_transformations": {
            "transformations": [
                {
                    "primitive_transformation": {
                        "replace_config": {
                            "new_value": {
                                "string_value":"[email-address]"
                            }
                        }
                    }
                }
            ]
        }
    }

    item = {"value": "email: jeff@jwdavis.me"}

    # Call the API
    response = dlp.deidentify_content(
        parent,
        inspect_config=inspect_config,
        deidentify_config=deidentify_config,
        item=item,
    )

    # Print out the results.
    return response.item.value