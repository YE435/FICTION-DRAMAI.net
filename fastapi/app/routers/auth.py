# routers/auth.py  # 토큰 검증 관련(공개키 제공 등)
from fastapi import APIRouter, HTTPException, Response
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/public-key")
def get_public_key():
    public_key = settings.JWT_PUBLIC_KEY or settings.SECRET_KEY
    if not public_key:
        raise HTTPException(status_code=500, detail="JWT public key not configured")

    headers = {"Cache-Control": "public, max-age=86400"}  # 24시간(초 단위) 캐싱 헤더 추가
    return Response(
        content=public_key,
        media_type="text/plain",
        headers=headers
    )

# auth 모듈 상태 확인 - JWT 키, 토큰 검증 로직 확인
@router.get("/health")
def auth_health_check():
    return {"status" : "auth ok"}
