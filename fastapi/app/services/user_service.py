# services/user_service.py
from app.clients.supabase_client import get_supabase
from app.schemas.user import UserCreate, UserUpdate
from app.utils.time_utils import now_utc_iso
from app.utils.security_utils import hash_password, verify_password
from app.core.logging import logger
supabase = get_supabase()
TABLE = "tb_user"

# 사용자 확인
def verify_user(user_id: str, user_pwd: str):
    # 1) 사용자 ID 조회
    res = supabase.table(TABLE).select("user_uuid, user_id, user_pwd").eq("user_id", user_id).execute()
    if not res.data:
        return None  # 없는 ID(이메일)

    user = res.data[0]

    # 2) 비밀번호 검증 (SHA256 기준)
    if not verify_password(user_pwd, user["user_pwd"]):
        return None
    
    return { 
        "user_uuid": user["user_uuid"],
        "user_id": user["user_id"]
    } # 확인한 사용자 정보(uuid, id) 반환

# 로그인
def login(user_id: str, user_pwd: str):
    # 1) 사용자 확인
    user = verify_user(user_id, user_pwd)
    if not user:
        return None  # 로그인 실패 or 비밀번호 불일치

    # 2) 로그인 성공 → last_logged_at 갱신
    now = now_utc_iso()
    supabase.table(TABLE).update({"last_logged_at": now}).eq("user_uuid", user["user_uuid"]).execute()

    return user["user_uuid"]  # 로그인 성공 시 사용자 uuid로 반환

# 회원 가입 - role 미입력 시 사용자
def signup(data: UserCreate):
     # 중복 사용자 확인
    existing = supabase.table(TABLE).select("user_id").eq("user_id", data.user_id).execute()
    if existing.data:
        return {"success": False, "message": "User ID already exists"}

    # 데이터 저장
    res = supabase.table(TABLE).insert({
        "user_id": data.user_id,
        # 비밀번호 암호화
        "user_pwd": hash_password(data.user_pwd),
        "nick": data.nick,
        "contact": data.contact,
        "role": data.role,
        "login_src" : data.login_src
    }).execute()

    if not res.data:
        return {"success": False, "message": "Signup failed"}

    user = res.data[0]
    user.pop("user_pwd", None)  # 전체 행 응답 시 비밀번호 제거
    return {"success": True, "data": user}

# 회원 정보 수정
def update_user(user_id: str, user_pwd, data: UserUpdate):

    # 1) 사용자 확인
    user = verify_user(user_id, user_pwd)
    if not user:
        return None  # 로그인 실패 or 비밀번호 불일치
    
    # 2) 정보 수정
    update_fields = data.model_dump(exclude_unset=True)
    update_fields["user_pwd"] = hash_password(data.user_pwd)
    res = supabase.table(TABLE).update(update_fields).eq("user_uuid", user["user_uuid"]).execute()
    return res.data[0] if res.data else None

# 전체 회원 조회
def list_users():
    res = supabase.table(TABLE).select("*").execute()
    return res.data

# 회원 uuid로 조회
def get_user(user_uuid):
    res = (
        supabase.table(TABLE)
        .select("user_uuid, user_id, nick, contact, role, last_logged_at, login_src, joined_at")
        .eq("user_uuid", user_uuid)
        .execute()
        )
    logger.info("get_user결과", res.data)
    return res.data[0]

# 회원 uuid로 삭제 # 수정 필요
def delete_user(user_uuid):
    res = (
        supabase.table(TABLE)
        .delete()
        .eq("user_uuid", user_uuid)
        .execute()
    )
    return bool(res.data)