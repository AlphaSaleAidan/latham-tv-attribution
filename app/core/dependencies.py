"""FastAPI dependency injection."""

from supabase import Client
from app.core.database import get_supabase


def get_db() -> Client:
    """Dependency: get Supabase client."""
    return get_supabase()
