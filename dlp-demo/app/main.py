"""
Modern Google Cloud DLP demonstration application.

This module provides a Flask web application that demonstrates Google Cloud
Data Loss Prevention (DLP) API capabilities including text inspection,
redaction, replacement, and masking of sensitive information.
"""

import os
import os
import sys
from typing import Any, Dict, Tuple

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Handle imports for both direct execution and module import
if __name__ == "__main__":
    # When run directly, add parent directory to path and use absolute imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.services.dlp_service import DLPService
    from app.config import Config
else:
    # When imported as a module, use relative imports
    from .services.dlp_service import DLPService
    from .config import Config

# Load environment variables
load_dotenv()


def create_app(config_class: type = Config) -> Flask:
    """Application factory pattern for creating Flask app instances.

    Args:
        config_class: Configuration class to use for the app

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for all domains and routes
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Initialize services with error handling
    dlp_service = None
    if app.config["GOOGLE_CLOUD_PROJECT"]:
        try:
            dlp_service = DLPService(project_id=app.config["GOOGLE_CLOUD_PROJECT"])
        except Exception as e:
            app.logger.warning(f"Failed to initialize DLP service: {str(e)}")
    else:
        app.logger.warning(
            "GOOGLE_CLOUD_PROJECT not configured - DLP functionality will be disabled"
        )

    @app.route("/")
    def index() -> str:
        """Serve the main DLP demo page."""
        return render_template("dlp-demo.html", title="DLP Demo 2.0")

    @app.route("/health")
    def health() -> Tuple[Dict[str, str], int]:
        """Health check endpoint for Cloud Run."""
        return {"status": "healthy"}, 200

    @app.route("/api/dlp", methods=["POST"])
    def process_dlp() -> Tuple[Dict[str, Any], int]:
        """Process text with DLP operations.

        Expected JSON payload:
        {
            "text": "Text to process",
            "action": "inspect|redact|replace|mask"
        }

        Returns:
            JSON response with DLP results
        """
        try:
            data = request.get_json()
            if not data or "text" not in data or "action" not in data:
                return {"error": "Missing required fields: text, action"}, 400

            text = data["text"]
            action = data["action"]

            if not text.strip():
                return {"error": "Text cannot be empty"}, 400

            # Check if DLP service is available
            if dlp_service is None:
                return {
                    "error": (
                        "DLP service not available - check GOOGLE_CLOUD_PROJECT configuration"
                    )
                }, 503

            if action == "inspect":
                result = dlp_service.inspect_text(text)
            elif action in ["redact", "replace", "mask"]:
                result = dlp_service.deidentify_text(text, action)
            else:
                return {"error": f"Invalid action: {action}"}, 400

            return {"result": result}, 200

        except Exception as e:
            app.logger.error(f"Error processing DLP request: {str(e)}")
            return {"error": "Internal server error"}, 500

    @app.errorhandler(404)
    def not_found(error: Any) -> Tuple[str, int]:
        """Handle 404 errors with a custom page."""
        return (
            render_template(
                "message.html",
                headline="404 - Page Not Found",
                message_text="The page you're looking for doesn't exist.",
                title="Not Found",
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(error: Any) -> Tuple[str, int]:
        """Handle 500 errors with a custom page."""
        return (
            render_template(
                "message.html",
                headline="500 - Internal Server Error",
                message_text="Something went wrong on our end.",
                title="Server Error",
            ),
            500,
        )

    return app


# Create app instance for gunicorn
app = create_app()


if __name__ == "__main__":
    # Development server
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_ENV") == "development"

    app.run(host="0.0.0.0", port=port, debug=debug)
