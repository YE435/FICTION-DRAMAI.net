# routers/rooms.py
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from app.schemas.room import RoomUpdate, RoomResponse, RoomSummary
from app.services import room_service
from app.deps.auth_deps import get_current_user_uuid
from app.utils.auth_utils import UnauthorizedAccessError
from typing import Optional
from app.core.logging import logger

router = APIRouter(prefix="/rooms", tags=["rooms"])


class RoomCreateRequest(BaseModel):
    charac_id: str


@router.post("/", response_model=RoomResponse, status_code=201)
def create_room(payload: RoomCreateRequest, user_uuid: str = Depends(get_current_user_uuid)):
    """
    전달받은 charac_id로 perchat 정보를 조회해 대화방을 생성한다.
    """
    try:
        return room_service.create_room(user_uuid, payload.charac_id)
    except room_service.PerchatNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Room creation failed: {exc}")

@router.get("/", response_model=list[RoomSummary])
def list_rooms(
    node_user_uuid: Optional[str] = Query(default=None, alias="user_uuid"),
    token_user_uuid: str = Depends(get_current_user_uuid)
):
    """
    로그인 된 사용자의 대화방 목록 조회
    - Node에서 전달된 user_uuid가 있으면 토큰과 일치 여부를 확인
    """
    if node_user_uuid and node_user_uuid != token_user_uuid:
        raise HTTPException(status_code=403, detail="User mismatch")

    return room_service.get_user_rooms_with_last_message(token_user_uuid)

@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: UUID,
    node_user_uuid: Optional[UUID] = Query(default=None, alias="user_uuid"),
    token_user_uuid: UUID = Depends(get_current_user_uuid)
):
    """
    특정 room_id에 대한 대화방 정보를 반환.
    Node로부터 전달된 user_uuid가 있으면 토큰과 일치하는지 확인.
    """
    logger.info(f"대화방 입장을 시도합니다")
    room_id = str(room_id)
    node_user_uuid = str(node_user_uuid)
    token_user_uuid = str(token_user_uuid)

    if node_user_uuid and node_user_uuid != token_user_uuid:
        raise HTTPException(status_code=403, detail="User mismatch")

    try:
        logger.info("uuid를 str로 넣어서 get_room 시도")
        room = room_service.get_room(room_id, token_user_uuid)
    except UnauthorizedAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except room_service.PerchatNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    logger.info("요청 성공 room 반환")
    return room

@router.get("/{search}", response_model=list[RoomResponse])
def search_rooms(search: str, user_uuid: str = Depends(get_current_user_uuid)):
    logger.info("검색어로 대화방을 찾습니다")
    return room_service.search_rooms(user_uuid, search)

@router.patch("/{room_id}", response_model=RoomResponse)
def update_room(room_id: str, room: RoomUpdate):
    updated = room_service.update_room(room_id, room)
    if not updated:
        raise HTTPException(status_code=404, detail="Room not found")
    return updated

@router.delete("/{room_id}")
def delete_room(room_id: str):
    success = room_service.delete_room(room_id)
    if not success:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"message": "Deleted successfully"}
