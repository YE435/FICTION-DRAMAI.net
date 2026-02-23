# schemas/script.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# 등록용 (POST)
class ScriptCreate(BaseModel):  # script_id는 DB에서 트리거가 알아서 입력
    drama_id: str
    episode_no: int
    scene_no: int
    script_no: int
    speaker: str
    dialogue: str
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
# 등록용 (POST; 드라마 제목 활용 대본 등록)
class ScriptInsertByTitle(BaseModel):  # script_id는 DB에서 트리거가 알아서 입력
    drama_title: str
    episode_no: int
    scene_no: int
    script_no: int
    speaker: str
    dialogue: str
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

# 수정용 (PATCH)
class ScriptUpdate(BaseModel):
    drama_id: Optional[str] = None
    episode_no: Optional[int] = None
    scene_no: Optional[int] = None
    script_no: Optional[int] = None
    speaker: Optional[str] = None
    dialogue: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

# 응답용
class ScriptResponse(BaseModel):
    script_id: str
    drama_id: str
    episode_no: int
    scene_no: int
    script_no: int
    speaker: str
    dialogue: str
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime