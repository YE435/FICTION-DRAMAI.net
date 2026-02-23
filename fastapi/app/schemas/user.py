# schemas/user.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

# 등록용 (POST)
class UserCreate(BaseModel):
    user_id: str
    user_pwd: str
    nick: str
    contact: str
    role: str = "user"
    login_src: Optional[str] = None

# 수정용 (PATCH)
class UserUpdate(BaseModel):
    user_pwd: Optional[str] = None
    nick: Optional[str] = None
    contact: Optional[str] = None
    login_src: Optional[str] = None

# 응답용
class UserResponse(BaseModel):
    user_uuid: UUID
    user_id: str
    nick: str
    contact: str
    role: str
    last_logged_at: Optional[datetime] = None
    login_src: Optional[str] = None
    joined_at: datetime

# 회원가입 응답용 # 가입 후 JWT 토큰 발급
class SignupResponse(BaseModel):
    user_uuid: UUID
    email: str
    nick: str
    access_token: str
    token_type: str = "bearer"

# 로그인 응답용 # 세션 기반 로그인
# class LoginResponse(BaseModel):
#     user_uuid: UUID
#     message: str = "Login successful"
    
# 로그인 요청용
class LoginRequest(BaseModel):
    user_id: str
    user_pwd: str

# 로그인 응답용 # JWT 기반 로그인    
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
