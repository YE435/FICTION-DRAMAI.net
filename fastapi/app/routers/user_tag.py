# routers/user_tag.py
from fastapi import APIRouter, HTTPException, Depends
from app.services import user_tag_service
from app.schemas.user_tag import UserTagRequest, UserTagResponse
from app.deps.auth_deps import get_current_user_uuid

router = APIRouter(prefix="/users", tags=["user-tags"])

def _process_payload(payload: UserTagRequest, token_user_uuid: str):
    if payload.user_uuid and payload.user_uuid != token_user_uuid:
        raise HTTPException(status_code=403, detail="User mismatch")

    result = user_tag_service.replace_user_tags(
        token_user_uuid,
        payload.drama_tags,
        payload.character_tags,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@router.post("/tags", response_model=UserTagResponse)
def create_user_tags(
    payload: UserTagRequest,
    user_uuid: str = Depends(get_current_user_uuid),
):
    return _process_payload(payload, user_uuid)


@router.patch("/tags", response_model=UserTagResponse)
def update_user_tags(
    payload: UserTagRequest,
    user_uuid: str = Depends(get_current_user_uuid),
):
    return _process_payload(payload, user_uuid)
