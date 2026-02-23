# routers/model_proxy.py # 프로토타입v1용 임시 라우트
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services import perchat_service, user_service, chat_db_service
from app.deps import auth_deps
from app.core.logging import logger
from app.model.perchat_yj import chat
router = APIRouter(prefix="/chat", tags=["chat"])

# 요청 스키마
class ChatRequest(BaseModel):
    message: str
    room_id: str

@router.post("/")
async def chat_with_model(
    req: ChatRequest,
    token_user_uuid: str = Depends(auth_deps.get_current_user_uuid)
):
    """
    사용자의 대화 요청을 받아:
    1) 캐릭터 정보 조회 → nick, perchat_id, perchat_name
    2) LLM 호출 후 결과 반환
    """
    logger.info("받은 요청 확인", req.message, req.room_id)
    # 1) 페르챗 정보 불러오기
    perchat_id = chat_db_service.load_perchat_by_room_id(req.room_id)["chatter"]
    logger.info(perchat_id)
    perchat = perchat_service.get_perchat(perchat_id)
    if not perchat:
        raise HTTPException(status_code=404, detail="페르챗을 찾을 수 없습니다.")
    logger.info("페르챗 정보 불러옴", perchat.keys())  # 에러 확인용 # 추후 삭제

    # 2) 사용자 nick 불러오기
    nick = user_service.get_user(token_user_uuid)["nick"]
    # 3) 필요 데이터 dict로 묶기
    data = {
        "user_uuid": str(token_user_uuid),
        "user_text": req.message,
        "room_id": req.room_id,
        "perchat_id": perchat_id,
        "nick": nick,
        "perchat_name": perchat["perchat_name"]
    }
    
    # 4) 모델 응답 생성
    res = await chat(data)
    logger.info(res)
    
    # 5) 결과 반환
    # return {"reply": reply, "character": char_data["charac_name"]}
    return res

