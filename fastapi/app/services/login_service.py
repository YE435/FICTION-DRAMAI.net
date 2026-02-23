from datetime import timedelta
from typing import Optional

from app.core.config import settings
from app.services import user_service
from app.utils.auth_utils import create_access_token


def authenticate_and_issue_token(user_id: str, user_pwd: str) -> Optional[dict]:
    """
    사용자 자격 증명을 확인하고 액세스 토큰을 발급.
    성공 시 토큰 정보(dict)를 반환하고, 실패 시 None 반환.
    """
    # 1) DB에서 사용자 조회 (성공 시 user_uuid 가져와 토큰 생성에 활용)
    user_uuid = user_service.login(user_id, user_pwd)
    if not user_uuid:
        return None

    # 2) user_uuid 활용하여 JWT 발급
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_uuid)},
        expires_delta=access_token_expires,
    )

    # 3) 토큰 반환
    return {"access_token": access_token, "token_type": "bearer"}
