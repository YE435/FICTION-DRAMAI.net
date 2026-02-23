# schemas/room.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

# 등록용 (POST)
class RoomCreate(BaseModel):
    room_title: str
    room_desc: str
    room_limit: int = 2
    user_uuid: Optional[UUID] = None  # 서버에서 채울 것
    room_status: str = "active"
    room_icon: Optional[str] = None

# 수정용 (PATCH)
class RoomUpdate(BaseModel):
    room_title: Optional[str] = None
    room_desc: Optional[str] = None
    room_limit: Optional[str] = None
    room_status: Optional[str] = None
    room_icon: Optional[str] = None

# 응답용
class RoomResponse(BaseModel):
    room_id: UUID
    room_title: str
    room_desc: str
    room_limit: int
    user_uuid: UUID
    room_status: str
    room_icon: Optional[str] = None
    created_at: datetime


class RoomSummary(BaseModel):
    id: UUID
    name: str
    avatar: Optional[str] = None
    lastMessage: Optional[str] = None
    createdAt: Optional[datetime] = None
