# deps/auth_deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.utils.auth_utils import verify_access_token

# JWT 토큰을 HTTP 헤더에서 자동 추출
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")  # 로그인 엔드포인트 경로

def get_current_user_uuid(token: str = Depends(oauth2_scheme)) -> str:
    """
    Authorization 헤더에서 JWT를 추출하고, 검증 후 user_uuid 반환
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_access_token(token)
    if not payload:
        raise credentials_exception

    user_uuid: str = payload.get("sub")
    if user_uuid is None:
        raise credentials_exception

    return user_uuid
