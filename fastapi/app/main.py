# main.py
# 25.10.27. 로깅 구성 담당 core/logging.py로 이동, 세션 미들웨어 삭제
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import dramas, characters, scripts, users, rooms, chattings, user_tag
from app.routers import model_proxy  # 프로토타입v1용 임시 라우트
from app.routers import login, auth  # 인증 관련 라우터

app = FastAPI(title="Supabase + FastAPI incl.scripts")

# CORS 설정 (Node/React와 통신 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:3000",  # React
        "http://localhost:4000"  # Node
    ],
    allow_credentials=True,  # 쿠키/세션 전달 허용
    allow_methods=["*"],
    allow_headers=["*"],
)

# 프로토타입v1용 임시 라우트
app.include_router(model_proxy.router)
                   #, prefix="/model", tags=["model"])

# 라우터 등록
app.include_router(login.router)
app.include_router(auth.router)
app.include_router(dramas.router)
app.include_router(characters.router)
app.include_router(scripts.router)
app.include_router(user_tag.router)
app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(chattings.router)

@app.get("/health")
def health_check():
    return {"status": "ok"} # 전체 서비스 가용성 확인

@app.get("/")
def root():
    return {"message": "FastAPI server is running"}
