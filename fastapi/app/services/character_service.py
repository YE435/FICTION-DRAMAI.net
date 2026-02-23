# services/character_service.py
from app.clients.supabase_client import get_supabase
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterInsertByTitle, CharacterUpdateByTitle
supabase = get_supabase()
TABLE = "tb_character"

# Create
def create_character(data: CharacterCreate):
    
    res = supabase.table(TABLE).insert({
        "charac_id": data.drama_id,
        "drama_id": data.drama_id,
        "charac_name": data.charac_name,
        "charac_desc": data.charac_desc,
        "actor": data.actor
    }).execute()

    return res.data[0]

# Create by drama_title
def insert_character_by_title(data: CharacterInsertByTitle):
    res = supabase.rpc(
        "insert_character_by_title",
        {
            "p_drama_title":data.p_drama_title,
            "p_charac_id":data.p_charac_id,
            "p_charac_name":data.p_charac_name,
            "p_charac_desc": data.p_charac_desc,
            "p_actor":data.p_actor 
        }
    ).execute()
    return res.data

# Read all
def list_characters():
    res = supabase.table(TABLE).select("*").execute()
    return res.data

# Read one
def get_character(charac_id: str):
    res = supabase.table(TABLE).select("*").eq("charac_id", charac_id).execute()
    if res.data:
        return res.data[0] # 라우터 안 거치면 그냥 dict 반환
    return None

# Update
def update_character(charac_id: str, data: CharacterUpdate):
    update_fields = data.model_dump(exclude_unset=True)
    res = supabase.table(TABLE).update(update_fields).eq("charac_id", charac_id).execute()
    if res.data:
        return res.data[0]
    return None
    
# Update by drama_title
def update_charac_by_title(data: CharacterUpdateByTitle):
    # None 값은 RPC 호출에서 제외 # 함수에서 오류 발생
    # params = {k: v for k, v in data.dict().items() if v is not None}
    # 명시적으로 null 전달 # 함수의 coalesce 때문에 null로 덮어쓰지 않고 기존 값을 사용함
    params = data.model_dump(exclude_unset=False)
    print(f"RPC PARAMS: {params}")

    res = supabase.rpc("update_character_by_title", params).execute()
    print(f"RPC ERROR: {res.data}")

    # Supabase RPC의 res.data는 리스트 형태로 반환 (ex: [1])
    if getattr(res, "status_code", None) == 200 and not res.error:
        updated_rows = res.data[0] if res.data else 0  # 반환값이 integer이므로 리스트 첫 원소 사용
        if updated_rows > 0:
            return {
                "success": True,
                "updated_rows": updated_rows,
                "message": f"{updated_rows} character(s) updated successfully",
            }
        else:
            return {
                "success": False,
                "updated_rows": 0,
                "message": "No matching character found for given title/name",
            }
    else:
        return {
            "success": False,   
            "updated_rows": 0,
            "message": "Update failed",
            "error": getattr(res, "error", None),
        }
    
    # res.data는 None (RETURNS void일 경우)
    # if getattr(res, "status_code", None) == 200 and not res.error:
    #     return {"success": True, "message": "Character updated successfully"}
    # else:
    #     return {"success": False, "message": "Update failed", "error": getattr(res, "error", None)}

# Delete
def delete_character(charac_id: str):
    res = supabase.table(TABLE).delete().eq("charac_id", charac_id).execute()
    return bool(res.data)