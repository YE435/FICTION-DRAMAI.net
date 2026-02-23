# routers/scripts.py # 삭제 예정
from fastapi import APIRouter, HTTPException
from app.schemas.script import ScriptCreate, ScriptUpdate, ScriptResponse
from app.services import script_service

router = APIRouter(prefix="/scripts", tags=["scripts"])

@router.post("/", response_model=ScriptResponse)
def create_script(script: ScriptCreate):
    return script_service.create_script(script)

@router.get("/", response_model=list[ScriptResponse])
def list_scripts():
    return script_service.list_scripts()

@router.get("/{script_id}", response_model=ScriptResponse)
def get_script(script_id: str):
    data = script_service.get_script(script_id)
    if not data:
        raise HTTPException(status_code=404, detail="Script not found")
    return data

@router.patch("/{script_id}", response_model=ScriptResponse)
def update_script(script_id: str, script: ScriptUpdate):
    updated = script_service.update_script(script_id, script)
    if not updated:
        raise HTTPException(status_code=404, detail="Script not found")
    return updated

@router.delete("/{script_id}")
def delete_script(script_id: str):
    success = script_service.delete_script(script_id)
    if not success:
        raise HTTPException(status_code=404, detail="Script not found")
    return {"message": "Deleted successfully"}
