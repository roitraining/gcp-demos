import google.cloud.dlp

def inspect(text):
    dlp = google.cloud.dlp_v2.DlpServiceClient()
    parent = dlp.project_path('roi-gcp-demos')
    
    inspect_config = {
        "info_types": [
            {"name": "EMAIL_ADDRESS"},
            {"name": "CREDIT_CARD_NUMBER"},
            {"name": "GENERIC_ID"},
            {"name": "IP_ADDRESS"},
            {"name": "PHONE_NUMBER"},
            {"name": "US_DRIVERS_LICENSE_NUMBER"},
            {"name": "US_SOCIAL_SECURITY_NUMBER"},
        ],
        "include_quote": True
    }

    item = {"value": text}

    # Call the API
    response = dlp.inspect_content(
        parent,
        inspect_config=inspect_config,
        item=item,
    )

    result = ""
    if response.result.findings:
        for finding in response.result.findings:
            try:
                if finding.quote:
                    result += "Quote: {}<br>".format(finding.quote)
            except AttributeError:
                pass
            result += "Info type: {}<br>".format(finding.info_type.name)
            result += "Likelihood: {}<br>".format(finding.likelihood)
            result += "<br>" 
    else:
        result = "No findings."
    return {"result": result}

def deidentify(text, action):

    if action == "mask":
        action = "character_mask"

    config = action + "_config"

    dlp = google.cloud.dlp_v2.DlpServiceClient()
    parent = dlp.project_path('roi-gcp-demos')
    
    inspect_config = {
        "info_types": [
            {"name": "EMAIL_ADDRESS"},
            {"name": "CREDIT_CARD_NUMBER"},
            {"name": "GENERIC_ID"},
            {"name": "IP_ADDRESS"},
            {"name": "PHONE_NUMBER"},
            {"name": "US_DRIVERS_LICENSE_NUMBER"},
            {"name": "US_SOCIAL_SECURITY_NUMBER"},
        ]
    }
    
    replace_config = {
        "new_value": {
            "string_value": "[REDACTED]"
        }
    }

    redact_config = {
    }

    character_mask_config = {
        "masking_character": "#",
        "number_to_mask": len(text) - 4,
        "characters_to_ignore": [
            {
                "characters_to_skip": "(),-/,@,."
            }
        ]
    }

    deidentify_config = {
        "info_type_transformations": {
            "transformations": [
                {
                    "primitive_transformation": {
                        config: locals()[config]
                    }
                }
            ]
        }
    }

    item = {"value": text}

    # Call the API
    response = dlp.deidentify_content(
        parent,
        inspect_config=inspect_config,
        deidentify_config=deidentify_config,
        item=item,
    )

    # Print out the results.
    return {
        "result": 
        "<br>".join(response.item.value.split("\n"))
    }