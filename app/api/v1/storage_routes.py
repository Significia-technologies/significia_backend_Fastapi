import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.schemas.storage_connector_schema import (
    StorageConnectorCreate,
    StorageConnectorResponse
)
from app.services.storage_service import StorageService
from app.database.remote_session import get_remote_session
from app.models.storage_connector import StorageConnector

router = APIRouter()

@router.get("/", response_model=List[StorageConnectorResponse])
def list_storage_connectors(
    db: Session = Depends(get_remote_session),
    current_user = Depends(get_current_user)
):
    return db.query(StorageConnector).all()

@router.post("/", response_model=StorageConnectorResponse)
def create_storage_connector(
    connector_in: StorageConnectorCreate,
    db: Session = Depends(get_remote_session),
    current_user = Depends(get_current_user)
):
    # Deactivate existing ones first
    db.query(StorageConnector).update({"is_active": False})
    
    return StorageService.create_storage_connector(db, current_user.tenant_id, connector_in.model_dump())

@router.post("/{storage_id}/verify")
async def verify_storage_connection(
    storage_id: uuid.UUID,
    db: Session = Depends(get_remote_session),
    current_user = Depends(get_current_user)
):
    success = await StorageService.test_and_verify_connector(db, storage_id, current_user.tenant_id)
    if not success:
        raise HTTPException(status_code=400, detail="Storage connection verification failed")
    return {"status": "success", "message": "Storage connection verified and activated"}
