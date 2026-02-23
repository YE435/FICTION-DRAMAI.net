# schemas/user_tag.py
from pydantic import BaseModel
from typing import List, Optional

class UserTagRequest(BaseModel):
    user_uuid: Optional[str] = None
    drama_tags: List[str]
    character_tags: List[str]


class UserTagResponse(BaseModel):
    success: bool
