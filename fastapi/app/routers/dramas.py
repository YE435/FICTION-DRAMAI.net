# routers/dramas.py
from fastapi import APIRouter, HTTPException
from app.schemas.drama import DramaCreate, DramaUpdate, DramaResponse
from app.services import drama_service

router = APIRouter(prefix="/dramas", tags=["dramas"])

@router.post("/", response_model=DramaResponse)
def create_drama(drama: DramaCreate):
    return drama_service.create_drama(drama)

@router.get("/", response_model=list[DramaResponse])
def list_dramas():
    return drama_service.list_dramas()

@router.get("/{drama_id}", response_model=DramaResponse)
def get_drama(drama_id: str):
    data = drama_service.get_drama(drama_id)
    if not data:
        raise HTTPException(status_code=404, detail="Drama not found")
    return data

@router.patch("/{drama_id}", response_model=DramaResponse)
def update_drama(drama_id: str, drama: DramaUpdate):
    updated = drama_service.update_drama(drama_id, drama)
    if not updated:
        raise HTTPException(status_code=404, detail="Drama not found")
    return updated

@router.delete("/{drama_id}")
def delete_drama(drama_id: str):
    success = drama_service.delete_drama(drama_id)
    if not success:
        raise HTTPException(status_code=404, detail="Drama not found")
    return {"message": "Deleted successfully"}
