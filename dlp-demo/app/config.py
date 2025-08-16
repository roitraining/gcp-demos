"""Configuration settings for the DLP demo application."""

import os


class Config:
    """Base configuration class."""

    # Google Cloud settings
    GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")

    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Application settings
    PORT = int(os.environ.get("PORT", 8080))

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        if not cls.GOOGLE_CLOUD_PROJECT:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
