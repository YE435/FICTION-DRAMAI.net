# routers/users.py
from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate, UserUpdate, UserResponse, SignupResponse
from app.services import user_service
from app.services.login_service import authenticate_and_issue_token
from app.core.logging import logger

router = APIRouter(prefix="/users", tags=["users"])

# 로그인 # JWT 기반 인증으로 변경하여 routers/login.py로 이동
# @router.post("/login", response_model=LoginResponse)
# def login(request: Request, user_id: str, user_pwd: str):
#     """
#     사용자 로그인
#     - ID(이메일)과 비밀번호를 검증
#     - 성공 시 최근 접속 시각 갱신
#     """
#     user_uuid = user_service.login(user_id, user_pwd)
#     if not user_uuid:
#         raise HTTPException(status_code=401, detail="Invalid user ID or password")
#     # 사용자 uuid 세션에 저장
#     request.session["user_uuid"] = str(user_uuid)
#     # # 보안상 비밀번호 필드는 제거
#     # user.pop("user_pwd", None)
#     return {"user_uuid": user_uuid}

# 회원 가입
@router.post("/signup", response_model=SignupResponse)
def signup(user: UserCreate):
    # 1) user 등록
    signup_result = user_service.signup(user)
    logger.info(f"insert성공 : {user}")
    if not signup_result.get("success"):
        raise HTTPException(status_code=400, detail=signup_result.get("message"))
    # 2) 로그인 로직 (JWT 발급)
    auth_result = authenticate_and_issue_token(user.user_id, user.user_pwd)
    if not auth_result or not auth_result.get("access_token"):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # jwt 토큰 전송 # react에서 localStorage에 저장
    return {
        "user_uuid": signup_result["data"]["user_uuid"],
        "email": signup_result["data"]["user_id"],
        "nick": signup_result["data"]["nick"],
        "access_token": auth_result.get("access_token"),
        "token_type": "bearer",
    }
    
# 회원 정보 수정
@router.patch("/update", response_model=UserResponse)
def update_user(user_id: str, user_pwd: str, data: UserUpdate):
    """
    사용자 정보 수정
    - user_id / user_pwd 로 본인 인증
    - 수정 가능한 필드는 UserUpdate 스키마에 정의됨
    """
    updated_user = user_service.update_user(user_id, user_pwd, data)
    if not updated_user:
        raise HTTPException(status_code=401, detail="Invalid user credentials or no user found")

    updated_user.pop("user_pwd", None)
    return updated_user

# 전체 사용자 조회
@router.get("/", response_model=list[UserResponse])
def list_users():
    return user_service.list_users()

# 사용자 id로 개별 사용자 조회
@router.post("/{user_uuid}", response_model=UserResponse)
def get_user(user_uuid: str):
    data = user_service.get_user(user_uuid)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return data[0]

# 사용자 계정 삭제 # 수정 필요
@router.delete("/{user_uuid}")
def delete_user(user_uuid: str):
    success = user_service.delete_user(user_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Deleted successfully"}
