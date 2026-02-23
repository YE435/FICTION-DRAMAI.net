from fastapi import APIRouter, HTTPException
from app.schemas.user import LoginRequest, LoginResponse
from app.services.login_service import authenticate_and_issue_token

router = APIRouter(prefix="/login", tags=["auth"])

@router.post("/", response_model=LoginResponse)
def login(data: LoginRequest):
    """
    사용자 로그인 (JWT 발급)
    - user_id, user_pwd를 검증 후 access_token 반환
    """
    token_payload = authenticate_and_issue_token(data.user_id, data.user_pwd)
    if not token_payload:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return token_payload
