# services/chatting_service.py
from app.clients.supabase_client import get_supabase
from app.schemas.chatting import ChattingCreate, ChattingUpdate
from app.utils.uuid_utils import new_uuid
from app.utils.time_utils import now_utc_iso
from app.utils.auth_utils import verify_room_owner, UnauthorizedAccessError
from app.core.logging import logger
from uuid import UUID
supabase = get_supabase()
TABLE = "tb_chatting"
TABLE_ROOM = "tb_room"

# 발화 저장 # 
# 사용자 발화는 라우터에서 # 페르챗 발화는 model 모듈 내부에서
def create_chat(data: dict):
    """
    발화를 DB에 기록
    chat_id는 자체적으로 생성 -> 기입 X
    room_id, chatter는 받은 정보 활용
    - 사용자 발화 저장 : 라우터에서 room_id, user_uuid 받아 옴
    - 페르챗 발화 저장 : model에서 room_id, perchat_id 받아 옴
    """
    res = supabase.table(TABLE).insert({
        "chat_id": str(new_uuid()),
        "room_id": data["room_id"],
        "chatter": data["chatter"],
        "chat_content": data["chat_content"],
        "chat_emoticon": data["chat_emoticon"],
        "chat_file": data["chat_file"],
        "role": data["role"],
        "turn_id": data["turn_id"],
        "meta_data": data["meta_data"]
    }).execute()

    return res.data[0]

# 해당 대화방의 모든 대화 내역 조회
def list_chat(room_id: str, user_uuid:str):
    # 방 소유자 검증
    verify_room_owner(room_id, user_uuid)
    
    # 방 O && 소유자 O -> 전체 대화 내역 반환
    res = (
        supabase.table(TABLE).select("*")
        .eq("room_id", room_id)
        .order("turn_id")
        .order("sent_at")
        .execute()
        )
    return res.data or []

# 해당 대화방의 최근 턴의 대화 내역 조회 # n<=0일 경우 전체 조회
def get_recent_chat_with_names(room_id: UUID, n: int = -1):
    """
    대화방의 최근 N턴 대화 내역을 시간 순서대로 조회
    발화자의 uuid(chatter)와 이름(name) 모두 포함
    """
    params = {"p_room_id": str(room_id), "p_limit_turn": n}
    logger.info(f"set params : {params}")
    res = supabase.rpc("get_recent_chat_with_names", params).execute()
    logger.info(f"{n}턴 조회 결과 : {res.data}")
    
    if getattr(res, "error", None):
        raise Exception(f"RPC error: {res.error}")
    return res.data or []

# 해당 대화방의 최근 N개 대화 내역 조회 # n<=0일 경우 전체 조회
def recent_chat_with_names(room_id: UUID, n: int = 15):
    """
    대화방의 최근 N개 대화 내역을 시간 순서대로 조회
    발화자의 uuid(chatter)와 이름(name) 모두 포함
    """
    params = {"p_room_id": room_id, "p_limit": n}
    logger.info(f"set params : {room_id}, {n}")
    res = supabase.rpc("recent_chat_with_names", params).execute()
    logger.info(f"{n}개 조회 결과 : {res.data}")
    
    if getattr(res, "error", None):
        raise Exception(f"RPC error: {res.error}")
    return res.data or []


# 쿼리 빌더 활용 조회 로직
# def recent_chat(room_id: str, n: int):
#     """
#     DB에서 최근 N개의 대화를 가져와 시간 순으로 정렬하여 반환
#     프론트/LLM 공용 사용 가능
#     """
#     res = (
#         supabase.table(TABLE)
#         .select("chatter, chat_content, chat_emoticon, chat_file, meta_data", "sent_at")
#         .eq("room_id", room_id)
#         .order("sent_at", desc=True)
#         .limit(n).execute()
#         )
#     # 보낸 시간 오름차순 정렬
#     chats = sorted(res.data or [], key=lambda x: x["sent_at"])
#     return chats
    
# 해당 대화방에서 검색어를 포함한 결과 조회 - chat_id, 내용, 날짜 반환
def search_chat(search: str, room_id: str, user_uuid: str):
    # 방 소유자 검증
    verify_room_owner(room_id, user_uuid)
    # 대화방에서 검색어로 발화 검색
    pattern = f"%{search}%"
    res = (
        supabase.table(TABLE)
        .select("chat_id, chat_content, sent_at")
        .eq("room_id", room_id)
        .ilike("chat_content", pattern)
        .order("sent_at", desc=True)
        .execute()
        )
    return res.data or []

# 채팅 내역 수정 (마지막 발화만 가능하게 하기)
def update_chat(chat_id: str, room_id: str, user_uuid: str, data: ChattingUpdate):
    # 방 소유자 검증
    verify_room_owner(room_id, user_uuid)
    # 대화방에서 가장 최근 발화의 chat_id인지 확인하기
    latest = (
        supabase.table(TABLE).select("chat_id")
        .eq("room_id", room_id)
        .order("sent_at", desc=True)
        .limit(1).execute()
        )
    if not latest.data or latest.data[0]["chat_id"] != chat_id:
        return {"error": "마지막 발화만 수정할 수 있습니다."}
    
    # 수정할 데이터 확인
    update_fields = {k: v for k, v in data.model_dump().items() if v is not None}
    update_fields["sent_at"] = now_utc_iso()
    
    # 마지막 발화 수정
    res = supabase.table(TABLE).update(update_fields).eq("chat_id", chat_id).execute()
    return res.data[0] if res.data else None

# 채팅 삭제 (가장 최신 내역부터 선택 발화까지 삭제)
def delete_chats_after_selected(room_id: str, chat_id: str, user_uuid: str):
    # 방 소유자 검증
    verify_room_owner(room_id, user_uuid)
    res = supabase.rpc(
        "delete_chats_after_selected",
        {"p_room_id": room_id, "p_chat_id": chat_id}
    ).execute()

    print(res)

    # 1) RPC 자체 오류 확인
    if getattr(res, "error", None):
        raise RuntimeError(f"RPC Error: {res.error}")

    # 2) 함수 결과값 확인 (함수가 count 반환 시)
    if not res.data or (isinstance(res.data, list) and not res.data[0]):
        return {"success": False, "message": "삭제된 발화가 없습니다."}

    # 3) 정상 삭제
    return {
        "success": True,
        "deleted_count": res.data,
        "message": "삭제가 완료되었습니다."
    }


# 채팅 삭제 (chat_id만 반영)
# def delete_chat(chat_id: str):
#     res = supabase.table(TABLE).delete().eq("chat_id", chat_id).execute()
#     return bool(res.data)
