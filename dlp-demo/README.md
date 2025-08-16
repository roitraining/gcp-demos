# DLP Demo 2.0

A Google Cloud Data Loss Prevention (DLP) demonstration application built for Cloud Run.

## Features

- **Modern Python**: Built with Python 3.11+ and type hints
- **Cloud Run Ready**: Containerized application with health checks
- **Application Default Credentials**: No service account keys needed
- **Modern Dependencies**: Up-to-date Flask, Google Cloud DLP, and other libraries
- **uv Package Management**: Fast and reliable dependency management
- **Best Practices**: Well-architected, documented, and tested

## Architecture

The application provides a web interface for demonstrating Google Cloud DLP capabilities:

- **Text Inspection**: Identify sensitive information in text
- **Data Redaction**: Remove sensitive information
- **Data Replacement**: Replace sensitive information with placeholders
- **Data Masking**: Mask sensitive information with characters

## Development Setup

1. Install uv if not already installed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up Google Cloud authentication:
   ```bash
   gcloud auth application-default login
   ```

4. Set environment variables:
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export PORT=8080
   ```

5. Run the development server:
   ```bash
   uv run python run.py
   ```

   Or alternatively:
   ```bash
   uv run python -m app.main
   ```

## Deployment

### Cloud Run

1. Build and deploy:
   ```bash
   gcloud run deploy dlp-demo \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

2. The service will automatically use the Cloud Run service account with appropriate permissions.

## Environment Variables

- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `PORT`: Port to run the application on (default: 8080)
- `FLASK_ENV`: Set to 'development' for debug mode

## API Endpoints

- `GET /`: Main DLP demo interface
- `POST /api/dlp`: Process text with DLP operations
- `GET /health`: Health check endpoint

## License

This project is for educational purposes as part of ROI Training's GCP demonstrations.
