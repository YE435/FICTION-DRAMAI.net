from __future__ import annotations
# app/services/chat_db_service.py
from typing import Dict, Any, List, Optional
from app.core.logging import logger
from app.clients.supabase_client import get_supabase

supabase = get_supabase()
TABLE = "tb_chatting"
TABLE_ROOM = "tb_room"
TABLE_PER = "tb_perchat"
TABLE_CHAR = "tb_character"
TABLE_EVENT = "tb_event" # 원작 사건 정리 기록
TABLE_STATE = "tb_chat_state" # 페르챗 현 시점 기록

# 페르챗 이름 -> perchat_id
def load_perchat_charac_id(name:str):
    res = supabase.table(TABLE_PER).select("perchat_id", "charac_id").eq("perchat_name", name).execute()
    return res.data[0]

# room_id로 페르챗 id 받아오기
def load_perchat_by_room_id(room_id:str):
    # perchat_id
    res = supabase.table(TABLE).select("chatter").eq("room_id", room_id).eq("role", 'you').order("turn_id", desc=True).limit(1).execute()
    if not res.data:
        return None
    return res.data[0]
# user_uuid로 사용자 nick 받아오기
def load_nick_by_room_id(user_uuid:str):
    # nick
    res = supabase.table(TABLE).select("nick").eq("user_uuid",user_uuid).limit(1).execute()
    if not res.data:
        return None
    return res.data[0]

# 여러 채팅 한 번에 입력(입출력 한 트랜잭션으로 저장)
def insert_chats_bulk(rows: List[Dict[str, Any]]) -> None:
    # 한 요청 = 한 트랜잭션(오토 커밋). 실패 시 예외 처리
    sb = get_supabase()
    res = sb.table(TABLE).insert(rows).execute()
    if getattr(res, "error", None):
        raise RuntimeError(res.error)

# 페르챗 이름 -> perchat_id, charac_id
def load_perchat_charac_id(name:str):
    res = supabase.table(TABLE_PER).select("perchat_id", "charac_id").eq("perchat_name", name).execute()
    return res.data[0]

# 넘겨받는 정보는 room_id와 user_uuid
# 이걸로 알아야 할 정보는 perchat_id, charac_id, user_nick
#=============== 입력 정보 ==================================
# user_id = "user_id_test"
# perchat_name = "유진 초이" # 페르챗 선택하는 걸로 가정
# turn_id = "1000"

# perchat_data = load_perchat_charac_id(perchat_name)
# # user_uuid = get_user(user_id)[0]["user_uuid"] # 라우터에서 token에서 추출해 보내줄 것
# user_nick = get_user(user_uuid)["nick"]
# perchat_id = perchat_data["perchat_id"]
# charac_id = perchat_data['charac_id']
#==========================================================

# 현재 상태 불러오기
def load_current_state(room_id: str):
    res = supabase.table(TABLE_STATE).select("*").eq("room_id", room_id).limit(1).execute()
    return res.data[0]

# 이벤트 불러오기 함수
def load_event(e_id:int, c_id:str):
    res = supabase.table(TABLE_EVENT).select("*").eq("event_id", e_id).eq("charac_id", c_id).execute()
    return res.data[0]

# 지금까지 일어난 일 불러오기
def load_past_memory(current_event_id:int, c_id:str):
    res = supabase.table(TABLE_EVENT).select("*").lt("event_id", current_event_id).eq("charac_id", c_id).order("event_id", desc=False).execute()
    return res.data

#----------------------------------------------------------------------------------------

from app.utils.time_utils import now_utc_iso
from pydantic import BaseModel, Field, field_validator
from typing import Optional

# 현재 상태 업데이트용 스키마 
class UpdateChatState(BaseModel):
    event_id: Optional[int] = None
    episode: Optional[int] = None
    location: Optional[str] = None
    time: Optional[str] = None
    updated_at: str = now_utc_iso()

# 현재 상태 업데이트 함수
def update_current_state(room_id:str, data:UpdateChatState):
    update_fields = data.model_dump(exclude_unset=True)
    res = supabase.table(TABLE_STATE).update(update_fields).eq("room_id", room_id).execute()
    if res.data:
        return res.data[0]
    return None

#----------------------------------------------------------------------------------------

def insert_chats_bulk(rows: List[Dict[str, Any]]) -> None:
    # 한 요청 = 한 트랜잭션(오토 커밋). 실패 시 예외 처리
    sb = get_supabase()
    res = sb.table("tb_chatting").insert(rows).execute()
    if getattr(res, "error", None):
        raise RuntimeError(res.error)

def load_docs_by_ids(ids: List[str]) -> List[Dict[str, Any]]:
    """RAG용 원문 로딩. 초기엔 단순화: chat_id로 tb_chatting 조회."""
    if not ids:
        return []
    sb = get_supabase()
    res = sb.table("tb_chatting").select("*").in_("chat_id", ids).execute()
    if getattr(res, "error", None):
        logger.warning("DB load_docs_by_ids error: %s", res.error)
        return []
    return res.data or []

# ✅ 2️⃣ load_all_event 불러오기 (이미 정의되어 있음)
def load_all_event(charac_id: str):
    res = (
        supabase.table("tb_event")
        .select("*")
        .eq("charac_id", charac_id)
        .order("event_id", desc=False)
        .execute()
    )
    return res.data

