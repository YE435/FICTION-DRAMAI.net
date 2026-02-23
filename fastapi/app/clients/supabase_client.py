# clients/supabase_client.py
from supabase import create_client, Client
from app.core.config import settings

_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is not None:
        return _supabase

    print("Supabase client 초기화 중...")
    _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return _supabase
