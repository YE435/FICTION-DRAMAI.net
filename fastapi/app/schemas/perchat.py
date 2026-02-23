# schemas/perchat.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

# 등록용 (POST)
class PerchatCreate(BaseModel):
    charac_id: str
    perchat_name: str
    prompt_full: Optional[str] = None
    greeting: Optional[str] = None

# 수정용 (PATCH)
class PerchatUpdate(BaseModel):
    charac_id: Optional[UUID] = None
    perchat_name: Optional[str] =None
    prompt_full: Optional[str] = None

# 응답용
class PerchatResponse(BaseModel):
    perchat_id: UUID
    charac_id: str
    perchat_name: str
    prompt_full: Optional[str] = None
    greeting: Optional[str] = None
    created_at: datetime