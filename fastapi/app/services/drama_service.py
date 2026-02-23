# services/drama_service.py
from app.clients.supabase_client import get_supabase
from app.schemas.drama import DramaCreate, DramaUpdate
supabase = get_supabase()
TABLE = "tb_drama"

# Create
def create_drama(data: DramaCreate):
    
    res = supabase.table(TABLE).insert({
        "drama_id": data.drama_id,
        "drama_title": data.drama_title,
        "drama_synop": data.drama_synop
    }).execute()

    return res.data[0]

# Read all
def list_dramas():
    res = supabase.table(TABLE).select("*").execute()
    return res.data

# Read one
def get_drama(drama_id: str):
    res = supabase.table(TABLE).select("*").eq("drama_id", drama_id).execute()
    if res.data:
        return res.data[0]
    return None

# Update
def update_drama(drama_id: str, data: DramaUpdate):
    update_fields = data.model_dump(exclude_unset=True)
    res = supabase.table(TABLE).update(update_fields).eq("drama_id", drama_id).execute()
    if res.data:
        return res.data[0]
    return None

# Delete
def delete_drama(drama_id: str):
    res = supabase.table(TABLE).delete().eq("drama_id", drama_id).execute()
    return bool(res.data)