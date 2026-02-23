# services/script_service.py
from app.clients.supabase_client import get_supabase
from app.schemas.script import ScriptCreate, ScriptUpdate, ScriptInsertByTitle
supabase = get_supabase()
TABLE = "tb_script"

# Create
def create_script(data: ScriptCreate):
    
    res = supabase.table(TABLE).insert({
        "drama_id": data.drama_id,
        "episode_no": data.episode_no,
        "scene_no": data.scene_no,
        "script_no": data.script_no,
        "speaker": data.speaker,
        "dialogue": data.dialogue,
        "meta_data": data.meta_data
    }).execute()

    return res.data[0]

# Create by drama_title
# def insert_script_by_title(data: ScriptInsertByTitle):
def insert_script_by_title(data):
    res = supabase.rpc(
        "insert_script_by_title",
		    {
		        "p_drama_title": data["drama_title"],
		        "p_episode_no": data["episode_no"],
		        "p_scene_no": data["scene_no"],
		        "p_script_no": data["script_no"],
		        "p_speaker": data["speaker"],
		        "p_dialogue": data["dialogue"],
		        "p_meta_data": data["meta_data"]
		    }
		).execute()
    return res.data

# Read all
def list_scripts():
    res = supabase.table(TABLE).select("*").execute()
    return res.data

# Read one
def get_script(script_id: str):
    res = supabase.table(TABLE).select("*").eq("script_id", script_id).execute()
    if res.data:
        return res.data[0]
    return None

# Update
def update_script(script_id: str, data: ScriptUpdate):
    update_fields = data.model_dump(exclude_unset=True)
    res = supabase.table(TABLE).update(update_fields).eq("script_id", script_id).execute()
    if res.data:
        return res.data[0]
    return None

# Delete
def delete_script(script_id: str):
    res = supabase.table(TABLE).delete().eq("script_id", script_id).execute()
    return bool(res.data)