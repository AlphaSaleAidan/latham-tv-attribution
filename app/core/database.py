"""Supabase database connection and helpers."""

from supabase import create_client, Client
from app.core.config import settings

_client: Client | None = None


def get_supabase() -> Client:
    """Get or create Supabase client singleton."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client


def health_check() -> bool:
    """Check if database connection is alive."""
    try:
        client = get_supabase()
        # Simple query to verify connection
        client.table("tv_airings").select("id", count="exact").limit(0).execute()
        return True
    except Exception:
        return False
