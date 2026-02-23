# services/room_service.py
from app.clients.supabase_client import get_supabase
from app.schemas.room import RoomUpdate
from app.utils.time_utils import now_utc_iso
from app.utils.uuid_utils import new_uuid
from app.core.logging import logger
supabase = get_supabase()
TABLE = "tb_room"
TABLE_CHAT = "tb_chatting"
TABLE_PERCHAT = "tb_perchat"

class PerchatNotFoundError(Exception):
    """perchat 정보를 찾을 수 없을 때 발생"""

# 새 대화방 insert문 # (+) 첫 대사 insert
def _insert_room(user_uuid: str, perchat_id: str, perchat_name: str, greeting: str):
    logger.info("새 대화방 insert 준비")
    timestamp = now_utc_iso()
    payload = {
        "room_title": perchat_name,
        "room_desc": f"{perchat_name}과의 대화 {timestamp}",
        "room_limit": 2,
        "user_uuid": user_uuid,
        "room_status": "active",
        "room_icon": None,
    }
    
    res = supabase.table(TABLE).insert(payload).execute()
    if not res.data:
        raise RuntimeError("Failed to create room")
    room_id = res.data[0]["room_id"]
    logger.info(f"방 생성 완료 : {room_id}")
    
    
    chat_res = supabase.table(TABLE_CHAT).insert({
        "chat_id": str(new_uuid()),
        "room_id": room_id,
        "chatter": perchat_id,
        "role": 'you',
        "turn_id": 0,
        "chat_content": greeting,
        "meta_data": '{}'
    }).execute()
    if not chat_res.data:
        raise RuntimeError("Failed to insert greeting message")
    chat_id = chat_res.data[0]["chat_id"]
    logger.info(f'첫 대사 입력 완료 : {chat_id}')
    return res.data[0]


# Create - 대화방 생성 (charac_id 기반-가장 먼저 생성된 perchat과의 대화방 생성)
def create_room(user_uuid: str, charac_id: str):
    logger.info("Creating room for user=%s charac_id=%s", user_uuid, charac_id)

    perchat_res = (
        supabase.table(TABLE_PERCHAT)
        .select("perchat_id, perchat_name, greeting")
        .eq("charac_id", charac_id)
        .order("created_at")
        .limit(1)
        .execute()
    )
    
    if not perchat_res.data:
        raise PerchatNotFoundError("Character not found for provided charac_id")

    perchat_id = perchat_res.data[0]["perchat_id"]
    perchat_name = perchat_res.data[0]["perchat_name"]
    greeting = perchat_res.data[0]["greeting"]
    logger.info(f"가져온 페르챗: {perchat_name}, {perchat_id}, {greeting}")
    return _insert_room(user_uuid, perchat_id, perchat_name, greeting)

# user_uuid와 perchat_id로 새 대화방 생성
def create_room_from_perchat(user_uuid: str, perchat_id: str):
    logger.info("Cloning room for user=%s using perchat_id=%s", user_uuid, perchat_id)

    # 페르챗 이름 가져오기 - 대화방 이름, 설명에 활용
    perchat_res = (
        supabase.table(TABLE_PERCHAT)
        .select("perchat_id, perchat_name, greeting")
        .eq("perchat_id", perchat_id)
        .limit(1)
        .execute()
    )

    logger.info(f"페르챗 확인: {perchat_res}")
    if not perchat_res.data:
        raise PerchatNotFoundError("Perchat not found for provided perchat_id")

    perchat_id = perchat_res.data[0]["perchat_id"]
    perchat_name = perchat_res.data[0]["perchat_name"]
    greeting = perchat_res.data[0]["greeting"]
    logger.info(f"가져온 페르챗: {perchat_name}, {perchat_id}, {greeting}")
    return _insert_room(user_uuid, perchat_id, perchat_name, greeting)

# 대화방 입장 요청 -> 사용자 확인 후 입장 or 새 대화방 생성 후 입장
def get_room(room_id: str, user_uuid: str):
    logger.info("Fetching room %s for user=%s", room_id, user_uuid)
    res = (
        supabase.table(TABLE)
        .select("*")
        .eq("room_id", room_id)
        .limit(1)
        .execute()
    )

    if not res.data:
        return None

    room = res.data[0]
    if room["user_uuid"] == user_uuid:
        logger.info("권한이 있는 입장을 허용합니다.")
        return room

    # 다른 사용자가 접근한 경우 → 첫 you 발화자의 perchat_id로 새 방 생성
    first_you = (
        supabase.table(TABLE_CHAT)
        .select("chatter")
        .eq("room_id", room_id)
        .eq("role", "you")
        .order("turn_id")
        .order("sent_at")
        .limit(1)
        .execute()
    )

    if not first_you.data:
        logger.info("시도하려는 대화방에서 페르챗을 찾지 못했습니다")
        raise PerchatNotFoundError("Cannot clone room without assistant history")

    perchat_id = first_you.data[0]["chatter"]
    logger.info(f"페르챗: {perchat_id}")
    if not perchat_id:
        logger.info("페르챗 id를 가져오지 못했습니다.")
        raise PerchatNotFoundError("Assistant perchat identifier missing for cloning")
    
    # 새 대화방 생성
    logger.info("새로운 대화방을 생성합니다.")
    new_room = create_room_from_perchat(user_uuid, perchat_id)
    
    return new_room

# 대화방 입장
def enter_or_clone_room(user_uuid: str, room_id: str):
    """
    사용자가 room_id로 접근했을 때
    1) 같은 유저면 기존 방의 채팅 내역 반환
    2) 다른 유저면 첫 발화자의 chatter를 기반으로 새로운 방 생성
    """

    # 1) 기존 room 정보 확인
    room_res = supabase.table(TABLE).select("*").eq("room_id", room_id).execute()
    if not room_res.data:
        return None
    room = room_res.data[0]

    # 2) 같은 유저인지 확인
    if room["user_uuid"] == user_uuid:
        # 기존 대화방의 전체 대화 내역 반환
        chats = (
            supabase.table(TABLE_CHAT)
            .select("*")
            .eq("room_id", room_id)
            .order("sent_at", desc=False)
            .execute()
        )
        return {
            "room_info": room,
            "chat_history": chats.data or [],
            "is_cloned": False,
        }

    # 3-1) 다른 유저일 경우 → 첫 발화자(chatter) 확인
    first_chat = (
        supabase.table(TABLE_CHAT)
        .select("chatter")
        .eq("room_id", room_id)
        .order("sent_at")
        .limit(1)
        .execute()
    )

    if not first_chat.data:
        return {"error": "No chat history found to clone"}

    first_chatter = first_chat.data[0]["chatter"]
    
    # 3-2) 새 room 생성
    new_room = {
        "user_uuid": user_uuid,
        "room_title": f"{first_chatter}", # 대화방 이름은 캐릭터 이름으로 수정 필요
        "room_desc": f"{first_chatter}과의 대화 {now_utc_iso()}", # 캐릭터 이름과 대화방 생성 시기 반영하여 수정 필요
        "room_status": "active"

    }

    supabase.table(TABLE).insert(new_room).execute()

    # 3-3) 반환 (빈 대화 내역 포함)
    return {
        "room_info": new_room,
        "chat_history": [],
        "is_cloned": True
    }

# 사용자가 참여 중인 모든 대화방('active') 조회 - 마지막 대화와 함께 반환
def get_user_rooms_with_last_message(user_uuid: str):
    res = supabase.rpc("get_user_rooms_with_last_message", {"p_user_uuid": user_uuid}).execute()
    rows =  res.data or []
    
    # front 요구 양식으로 맞추기
    results = []
    for room in rows:
        results.append({
            "id": room["room_id"],
            "name": room.get("room_title"),
            "avatar": room.get("room_icon"),
            "lastMessage": room.get("last_message"),
            "createdAt": room.get("last_sent_at")
        })

    return results

# Read all - 사용자 참여 대화방 조회 # tb_room의 정보들만 반환 list_rooms_with~ 함께 수행 필요
# def list_rooms(user_uuid: str):
#     """
#     user_uuid를 인자로 받아 해당 사용자의 활성화된 대화방 목록을 반환
#     """
#     res = (
#         supabase.table(TABLE).select("*")
#         .eq("user_uuid", user_uuid)
#         .eq("room_status", 'active')
#         .order("created_at", desc=True)
#         .execute()
#         )
#     return res.data or []


# def list_rooms_with_last_message(user_uuid: str):
#     """
#     사용자 대화방 목록과 각 방의 마지막 메시지를 반환.
#     """
#     rooms = list_rooms(user_uuid)
#     results = []

#     for room in rooms:
#         last_chat = (
#             supabase.table(TABLE_CHAT)
#             .select("chat_content, sent_at, turn_id")
#             .eq("room_id", room["room_id"])
#             .order("turn_id", desc=True)
#             .order("sent_at", desc=True)
#             .limit(1)
#             .execute()
#         )

#         last = last_chat.data[0] if last_chat.data else None
#         results.append({
#             "id": room["room_id"],
#             "name": room.get("room_title"),
#             "avatar": room.get("room_icon"),
#             "lastMessage": last.get("chat_content") if last else None,
#             "createdAt": last.get("sent_at") if last else room.get("created_at"),
#         })

#     return results

# Read by Perchat - 사용자가 특정 페르챗과 대화한 기록 조회


# Read by searching - 대화방 검색
def search_rooms(user_uuid: str, search: str):
    """
    현재 로그인한 사용자의 활성화된 대화방 목록 중
    입력된 검색어를 포함하는 모든 대화방 목록을 반환
    (빈 문자열 입력 시 전체 대화방 목록 반환)
    """
    pattern = f"%{search}%"
    res = (
        supabase.table(TABLE)
        .select("*")
        .or_(
            f"and(user_uuid.eq.{user_uuid},room_status.eq.active,room_title.ilike.{pattern}),"
            f"and(user_uuid.eq.{user_uuid},room_status.eq.active,room_desc.ilike.{pattern})"
        )
        .order("created_at", desc=True)
        .execute()
        )
    return res.data or []


# Update
def update_room(room_id: str, data: RoomUpdate):
    update_fields = data.dict(exclude_unset=True)
    res = supabase.table(TABLE).update(update_fields).eq("room_id", room_id).execute()
    if not res.data:
        return None
    return res.data[0]

# Delete
def delete_room(room_id: str):
    res = supabase.table(TABLE).delete().eq("room_id", room_id).execute()
    return bool(res.data)
