# schemas/character.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# 등록용 (POST)
class CharacterCreate(BaseModel):
    charac_id: str
    drama_id: str
    charac_name: str
    charac_desc: str
    actor: str
    
# 등록용 (POST; 드라마 제목 활용 캐릭터 등록)
class CharacterInsertByTitle(BaseModel):
    p_drama_title: str
    p_charac_id: str
    p_charac_name: str
    p_charac_desc: str
    p_actor: str

# 수정용 (PATCH)
class CharacterUpdate(BaseModel):
    drama_id: Optional[str] = None
    charac_id: Optional[str] = None
    charac_name: Optional[str] = None
    charac_desc: Optional[str] = None
    actor: Optional[str] = None

# 수정용 (PATCH; 드라마 제목 활용 캐릭터 수정)
class CharacterUpdateByTitle(BaseModel):
    p_drama_title: str
    p_charac_name: str
    p_charac_id: Optional[str] = None
    p_charac_desc: Optional[str] = None
    p_actor: Optional[str] = None

# 응답용
class CharacterResponse(BaseModel):
    charac_id: str
    drama_id: str
    charac_name: str
    charac_desc: str
    actor: str
    created_at: datetime