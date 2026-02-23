# services/perchat_service.py
from fastapi import HTTPException
from app.clients.supabase_client import get_supabase
from app.schemas.perchat import PerchatCreate, PerchatUpdate, PerchatResponse
supabase = get_supabase()
TABLE = "tb_perchat"

def create_perchat(data: PerchatCreate):
    res = supabase.table(TABLE).insert({
        "charac_id": data.charac_id,
        "perchat_name": data.perchat_name,
        "prompt_full": data.prompt_full,
        "greeting" : data.greeting
    }).execute()

    return res.data[0]

# 페르챗ID로 조회
def get_perchat(perchat_id: str):
    res = supabase.table(TABLE).select("*").eq("perchat_id", perchat_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Perchat not found")
    return res.data[0]

# 캐릭터ID로 기본 페르챗 조회
def get_perchat_by_charac_id(charac_id: str):
    res = supabase.table(TABLE).select("*").eq("charac_id", charac_id).order("created_at").limit(1).execute()
    return res.data[0] # 객체(dict)로 반환