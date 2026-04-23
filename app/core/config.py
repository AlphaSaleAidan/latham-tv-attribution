"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from .env file."""

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    # Google Analytics 4
    ga4_property_id: Optional[str] = None
    ga4_credentials_path: Optional[str] = None

    # Google Search Console
    gsc_site_url: Optional[str] = None

    # CallRail
    callrail_api_key: Optional[str] = None
    callrail_account_id: Optional[str] = None

    # QR Code Tracking
    flowcode_api_key: Optional[str] = None
    bitly_access_token: Optional[str] = None

    # SEMrush
    semrush_api_key: Optional[str] = None

    # Google Trends config
    trends_search_terms: list[str] = [
        "latham pools",
        "latham pool",
        "latham",
        "fiberglass pool",
        "inground pool",
    ]
    trends_rate_limit_delay: float = 3.0  # seconds between requests

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
