# schemas/chatting.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import json

# 등록용 (POST)
class ChattingCreate(BaseModel):
    chat_id: Optional[UUID] = None # 서버에서 채울 것
    room_id: Optional[UUID] = None # 서버에서 채울 것
    chatter: Optional[UUID] = None # 서버에서 채울 것
    chat_content: Optional[str] = None
    chat_emoticon: Optional[str] = None
    chat_file: Optional[str] = None
    role: Optional[str] = None
    turn_id: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = {}
    sent_at: Optional[datetime] = None

# 수정용 (PATCH)
class ChattingUpdate(BaseModel):
    chatter: Optional[UUID] = None
    chat_content: Optional[str] = None
    chat_emoticon: Optional[str] = None
    chat_file: Optional[str] = None
    role: Optional[str] = None
    turn_id: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

# 응답용
class ChattingResponse(BaseModel):
    chat_id: UUID
    room_id: Optional[UUID]
    chatter: Optional[UUID]
    chat_content: str
    chat_emoticon: Optional[str] = None
    chat_file: Optional[str] = None
    role: Optional[str] = None
    turn_id: Optional[int] = None
    meta_data: Optional[Dict[str, Any]]
    sent_at: Optional[datetime]
    
    @field_validator("meta_data", mode="before")
    def parse_meta_data(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v
    
# 프론트 응답용
class ChattingResponseWithName(BaseModel):
    name : str