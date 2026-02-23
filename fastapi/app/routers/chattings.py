# routers/chattings.py
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from app.schemas.chatting import ChattingCreate, ChattingUpdate, ChattingResponse, ChattingResponseWithName
from app.services import chatting_service
from app.deps.auth_deps import get_current_user_uuid
from app.utils.auth_utils import UnauthorizedAccessError
from app.core.logging import logger
from uuid import UUID

router = APIRouter(prefix="/chat", tags=["chat"])

# model_proxy.py에서 응답 받는 용도로 사용 중 추후 기능 분리 후 수정
# @router.post("/", response_model=ChattingResponse)
# def create_chat(
#     chatting: ChattingCreate, 
#     room_id: str = Query(..., description="대화방 ID"), 
#     user_uuid: str = Depends(get_current_user_uuid)
# ):
#     """
#     사용자가 입력한 입력한 발화를 기록
#     - Query Param에서 room_id를 가져오고
#     - JWT 토큰에서 사용자의 uuid를 가져와서 insert
#     """
#     data = chatting.model_dump()
#     data["room_id"] = room_id
#     data["chatter"] = user_uuid
#     return chatting_service.create_chat(data)

# 현재 대화방의 대화 내역 조회 - chat_id, room_id, chatter, name, 내용, 날짜 반환
# GET /chat/{room_id}
@router.get("/{room_id}", response_model=List[Dict[str, Any]])
def get_recent_chat_with_names(
    room_id: UUID, 
    node_user_uuid: str = Query(..., description="사용자UUID"), 
    n:int = Query(default=-1, description="최근 n개 혹은 전체(-1) 내역 조회"), 
    token_user_uuid: str = Depends(get_current_user_uuid)
):
    """
    현재 대화방의 대화 내역 조회
    - n>0 : 최근 n턴, n<0 : 전체
    - room_id는 URL path param
    - node_user_uuid는 node에서 보냄
    - token_user_uuid는 JWT 토큰에서 직접 추출
    """
    if node_user_uuid and node_user_uuid != token_user_uuid:
        raise HTTPException(status_code=403, detail="User mismatch")    
    
    try:
        logger.info("대화 내역 조회 시도")
        result = chatting_service.get_recent_chat_with_names(room_id, n)
        # return result
        
        # 프론트 요구 형식으로 변환
        formatted = [
            {
                "id": r["chatter"],
                "name": r["name"],
                "from": r["role"],
                "text": r["chat_content"],
            }
            for r in result
        ]
        return formatted
    except UnauthorizedAccessError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# 대화방에서 발화 검색 
# GET /chat?search=검색어&room_id={room_id}
@router.get("/", response_model=list[ChattingResponse])
def search_chat(
    search: str = Query(..., description="사용자가 입력한 검색어"),
    room_id: str = Query(..., description="대화방 ID")
):
    try:
        logger.info("대화 검색 시도(쿼리)")
        result = chatting_service.search_chat(room_id, search)
        return result
    except UnauthorizedAccessError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# 마지막 발화 수정
@router.patch("/", response_model=ChattingResponse)
def update_chat(
    chat_id: str = Query(..., description="수정할 발화의 ID"),
    room_id: str = Query(..., description="대화방 ID"),
    data: ChattingUpdate = None,
    user_uuid: str = Depends(get_current_user_uuid)
):
    """
    현재 대화방의 마지막 발화만 수정
    - chat_id, room_id는 쿼리 파라미터로 전달
    - user_uuid는 세션에서 확인
    """
    try:
        result = chatting_service.update_chat(chat_id, room_id, user_uuid, data)
        if not result:
            raise HTTPException(status_code=400, detail="수정 실패 또는 데이터 없음")
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except UnauthorizedAccessError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# 선택~마지막 발화까지 삭제
@router.delete("/")
def delete_chats_after_selected(
    chat_id: str = Query(..., description="삭제 기준 발화 ID"),
    room_id: str = Query(..., description="대화방 ID"),
    user_uuid: str = Depends(get_current_user_uuid)
):
    """
    현재 대화방의 마지막 발화부터 선택한 발화까지 삭제
    - chat_id, room_id는 쿼리 파라미터로 전달
    - user_uuid는 세션에서 확인
    """
    try:
        result = chatting_service.delete_chats_after_selected(room_id, chat_id, user_uuid)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

# @router.patch("/{chat_id}", response_model=ChattingResponse)
# def update_chat(chat_id: str, chatting: ChattingUpdate, room_id: str = Query):
#     updated = chatting_service.update_chat(chat_id, room_id, chatting)
#     if not updated:
#         raise HTTPException(status_code=404, detail="Chatting not found")
#     return updated
# @router.delete("/{chat_id}")
# def delete_chats_after_selected(chat_id: str, room_id: str):
#     success = chatting_service.delete_chats_after_selected(room_id, chat_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="Chatting not found")
#     return success