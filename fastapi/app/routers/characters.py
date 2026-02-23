# routers/characters.py
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterResponse, CharacterInsertByTitle, CharacterUpdateByTitle
from app.services import character_service
from uuid import UUID

router = APIRouter(prefix="/characters", tags=["characters"])

@router.post("/", response_model=CharacterResponse)
def create_character(character: CharacterCreate):
    return character_service.create_character(character)

@router.post("/insert_by_title")
def insert_character_by_title(data: CharacterInsertByTitle):
    return character_service.insert_character_by_title(data)

@router.get("/", response_model=list[CharacterResponse])
def list_characters():
    return character_service.list_characters()

@router.get("/{charac_id}", response_model=CharacterResponse)
def get_character(charac_id: str):
    data = character_service.get_character(charac_id)
    if not data:
        raise HTTPException(status_code=404, detail="Character not found")
    return data

@router.patch("/ud_by_title")
def update_charac_by_title(data: CharacterUpdateByTitle):
    result = character_service.update_charac_by_title(data)
    return result

@router.patch("/{charac_id:uuid}", response_model=CharacterResponse)
def update_character(charac_id: UUID, character: CharacterUpdate):
    updated = character_service.update_character(charac_id, character)
    if not updated:
        raise HTTPException(status_code=404, detail="Character not found")
    return updated

@router.delete("/{charac_id}")
def delete_character(charac_id: str):
    success = character_service.delete_character(charac_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"message": "Deleted successfully"}
