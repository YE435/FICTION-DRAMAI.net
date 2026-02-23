# schemas/drama.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# 등록용 (POST)
class DramaCreate(BaseModel):
    drama_id: str
    drama_title: str
    drama_synop: str

# 수정용 (PATCH)
class DramaUpdate(BaseModel):
    drama_id: Optional[str] = None
    drama_title: Optional[str] = None
    drama_synop: Optional[str] = None

# 응답용
class DramaResponse(BaseModel):
    drama_id: str
    drama_title: str
    drama_synop: str
    created_at: datetime