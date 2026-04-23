"""Supabase database connection and helpers."""

from supabase import create_client, Client
from app.core.config import settings

_client: Client | None = None


def get_supabase() -> Client:
    """Get or create Supabase client singleton."""
    global _client
    if _client is None:
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError(
                f"Missing Supabase config: url={'set' if settings.supabase_url else 'EMPTY'}, "
                f"service_key={'set' if settings.supabase_service_key else 'EMPTY'}"
            )
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client


def health_check() -> dict:
    """Check if database connection is alive. Returns dict with status and any error."""
    try:
        client = get_supabase()
        client.table("tv_airings").select("id", count="exact").limit(0).execute()
        return {"connected": True, "error": None}
    except Exception as e:
        return {"connected": False, "error": f"{type(e).__name__}: {str(e)[:200]}"}
