# utils/auth_utils.py
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings  # 키/알고리즘 설정
from app.clients.supabase_client import get_supabase
from app.core.logging import logger
from cryptography.hazmat.primitives import serialization # pem 포맷 키 열기

# RSA 기반 키/알고리즘 설정 (config 활용)
JWT_PRIVATE_KEY = settings.JWT_PRIVATE_KEY.replace("\\n", "\n")
JWT_PUBLIC_KEY = settings.JWT_PUBLIC_KEY.replace("\\n", "\n")
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_PRIVATE_KEY_PASSWORD = settings.JWT_PRIVATE_KEY_PASSWORD

# 토큰 생성 
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    주어진 payload(data)에 대해 RS256 알고리즘으로 JWT 액세스 토큰을 생성합니다.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    # PEM 문자열을 bytes로 인코딩
    private_key_bytes = JWT_PRIVATE_KEY.encode()

    private_key = serialization.load_pem_private_key(
        private_key_bytes,
        password=JWT_PRIVATE_KEY_PASSWORD.encode() or None
    )
    # 비밀키 활용 인코딩
    encoded_jwt = jwt.encode(to_encode, private_key, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# 토큰 검증
def verify_access_token(token: str):
    """
    전달받은 JWT 토큰을 RS256 공개키로 검증합니다.
    검증 실패 시 None을 반환합니다.
    """
    # PEM 문자열 → key object 로드
    public_key = serialization.load_pem_public_key(
        JWT_PUBLIC_KEY.encode()
    )
    try:
        payload = jwt.decode(token, public_key, algorithms=[JWT_ALGORITHM])
        return payload  # {"sub": user_id, "exp": ...}
    except jwt.ExpiredSignatureError:
        logger.warning("❌ 만료된 토큰입니다.")
        return None
    except jwt.InvalidTokenError:
        logger.warning("❌ 유요하지 않은 토큰입니다.")
        return None
    # except jwt.PyJWTError:
    #     return None

# --- supabase 클라이언트 및 접근 제어 ---
supabase = get_supabase()

class UnauthorizedAccessError(Exception):
    """사용자 접근 권한이 없을 때 발생"""
    pass


def verify_room_owner(room_id: str, user_uuid: str) -> None:
    """
    주어진 room_id가 현재 사용자(user_uuid)의 소유인지 검증
    - room_id가 없거나 user_uuid가 다르면 UnauthorizedAccessError 발생
    """
    res = supabase.table("tb_room").select("user_uuid").eq("room_id", room_id).execute()

    if not res.data:
        raise UnauthorizedAccessError("해당 대화방을 찾을 수 없습니다.")

    owner_uuid = res.data[0]["user_uuid"]
    if owner_uuid != user_uuid:
        raise UnauthorizedAccessError("접근할 수 없는 대화방입니다.")
