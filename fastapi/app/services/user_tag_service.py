# services/user_tag_service.py
from app.clients.supabase_client import get_supabase

supabase = get_supabase()


def replace_user_tags(user_uuid: str, drama_tags, character_tags):
    all_tags = list(dict.fromkeys((drama_tags or []) + (character_tags or [])))

    if not all_tags:
        return {"success": True, "inserted": 0}

    tag_query = (
        supabase.table("tb_tag")
        .select("tag_id")
        .in_("tag_name", all_tags)
        .execute()
    )

    if not tag_query.data:
        return {"success": False, "message": "No matching tags found"}

    supabase.table("tb_user_tag").delete().eq("user_uuid", user_uuid).execute()

    inserts = [{"user_uuid": user_uuid, "tag_id": t["tag_id"]} for t in tag_query.data]
    insert_res = supabase.table("tb_user_tag").insert(inserts).execute()

    if insert_res.data is None:
        return {"success": False, "message": "Insert failed"}

    return {"success": True, "inserted": len(insert_res.data)}
