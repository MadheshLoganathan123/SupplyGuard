"""
Supabase client — singleton instances for anon and service-role access.

Usage:
    from app.database.supabase_client import supabase, supabase_admin

    # Public / anon key (respects RLS policies)
    data = supabase.table("shipments").select("*").execute()

    # Service-role key (bypasses RLS — use only in trusted server code)
    data = supabase_admin.table("shipments").select("*").execute()
"""

from supabase import Client, create_client

from app.core.config import settings

# Anon client — safe to use in user-facing operations (respects Row Level Security)
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_ANON_KEY,
)

# Admin client — bypasses RLS; use only in internal/server-side operations
supabase_admin: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY,
)
