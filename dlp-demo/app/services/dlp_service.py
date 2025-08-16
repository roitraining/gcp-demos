"""
Google Cloud DLP service wrapper.

This module provides a clean interface to Google Cloud DLP API for
text inspection and de-identification operations.
"""

from typing import Dict, List, Any, Optional
import logging

from google.cloud import dlp_v2

logger = logging.getLogger(__name__)


class DLPService:
    """Service class for Google Cloud DLP operations."""

    # Standard info types to detect
    DEFAULT_INFO_TYPES = [
        "EMAIL_ADDRESS",
        "CREDIT_CARD_NUMBER",
        "GENERIC_ID",
        "IP_ADDRESS",
        "PHONE_NUMBER",
        "US_DRIVERS_LICENSE_NUMBER",
        "US_SOCIAL_SECURITY_NUMBER",
        "PERSON_NAME",
        "US_PASSPORT",
        "DATE_OF_BIRTH",
    ]

    def __init__(self, project_id: str, info_types: Optional[List[str]] = None):
        """Initialize the DLP service.

        Args:
            project_id: Google Cloud project ID
            info_types: List of info types to detect (uses defaults if None)
        """
        self.project_id = project_id
        self.info_types = info_types or self.DEFAULT_INFO_TYPES
        self.client = dlp_v2.DlpServiceClient()
        self.parent = f"projects/{project_id}"

        logger.info(f"Initialized DLP service for project: {project_id}")

    def inspect_text(self, text: str) -> str:
        """Inspect text for sensitive information.

        Args:
            text: Text to inspect

        Returns:
            HTML-formatted string with inspection results
        """
        try:
            # Configure inspection
            inspect_config = {
                "info_types": [{"name": info_type} for info_type in self.info_types],
                "include_quote": True,
                "min_likelihood": "POSSIBLE",
            }

            item = {"value": text}

            # Call the API
            response = self.client.inspect_content(
                request={
                    "parent": self.parent,
                    "inspect_config": inspect_config,
                    "item": item,
                }
            )

            # Format results
            if response.result.findings:
                result_parts = []
                for finding in response.result.findings:
                    parts = []
                    if finding.quote:
                        parts.append(f"<strong>Quote:</strong> {finding.quote}")
                    parts.append(
                        f"<strong>Info type:</strong> {finding.info_type.name}"
                    )
                    parts.append(
                        f"<strong>Likelihood:</strong> {finding.likelihood.name}"
                    )

                    if finding.location.byte_range.start:
                        start = finding.location.byte_range.start
                        end = finding.location.byte_range.end
                        parts.append(f"<strong>Location:</strong> {start}-{end}")

                    result_parts.append("<br>".join(parts))

                return "<br><br>".join(result_parts)
            else:
                return "<em>No sensitive information detected.</em>"

        except Exception as e:
            logger.error(f"Error inspecting text: {str(e)}")
            return f"<em>Error during inspection: {str(e)}</em>"

    def deidentify_text(self, text: str, action: str) -> str:
        """De-identify sensitive information in text.

        Args:
            text: Text to de-identify
            action: Type of de-identification ('redact', 'replace', 'mask')

        Returns:
            HTML-formatted string with de-identified text
        """
        try:
            # Configure inspection
            inspect_config = {
                "info_types": [{"name": info_type} for info_type in self.info_types]
            }

            # Configure transformation based on action
            if action == "redact":
                transformation = {"redact_config": {}}
            elif action == "replace":
                transformation = {
                    "replace_config": {"new_value": {"string_value": "[REDACTED]"}}
                }
            elif action == "mask":
                transformation = {
                    "character_mask_config": {
                        "masking_character": "#",
                        "number_to_mask": 0,  # Mask all characters
                        "characters_to_ignore": [{"characters_to_skip": "(),-/@."}],
                    }
                }
            else:
                raise ValueError(f"Unsupported action: {action}")

            # Configure de-identification
            deidentify_config = {
                "info_type_transformations": {
                    "transformations": [{"primitive_transformation": transformation}]
                }
            }

            item = {"value": text}

            # Call the API
            response = self.client.deidentify_content(
                request={
                    "parent": self.parent,
                    "inspect_config": inspect_config,
                    "deidentify_config": deidentify_config,
                    "item": item,
                }
            )

            # Return formatted result
            result_text = response.item.value
            return "<br>".join(result_text.split("\n"))

        except Exception as e:
            logger.error(f"Error de-identifying text with action '{action}': {str(e)}")
            return f"<em>Error during {action}: {str(e)}</em>"
