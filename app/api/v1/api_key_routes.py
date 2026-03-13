from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import secrets
import hashlib

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.api_key import ApiKey
from app.schemas.api_key_schema import ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse, ApiKeyUpdate

router = APIRouter()

def generate_api_key() -> tuple[str, str]:
    """Generates a plain key and its sha256 hash"""
    plain_key = f"sig_{secrets.token_urlsafe(32)}"
    hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()
    return plain_key, hashed_key

@router.post("/", response_model=ApiKeyCreateResponse)
def create_api_key(
    key_in: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User does not belong to a tenant")
        
    plain_key, hashed_key = generate_api_key()
    
    db_key = ApiKey(
        tenant_id=current_user.tenant_id,
        hashed_key=hashed_key,
        name=key_in.name,
        allowed_domains=key_in.allowed_domains
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    
    # We return plain_key ONLY this one time
    return ApiKeyCreateResponse(
        id=db_key.id,
        tenant_id=db_key.tenant_id,
        name=db_key.name,
        allowed_domains=db_key.allowed_domains,
        is_active=db_key.is_active,
        created_at=db_key.created_at,
        plain_key=plain_key
    )

@router.get("/", response_model=List[ApiKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User does not belong to a tenant")
        
    return db.query(ApiKey).filter(ApiKey.tenant_id == current_user.tenant_id).all()

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_key = db.query(ApiKey).filter(
        ApiKey.id == key_id, 
        ApiKey.tenant_id == current_user.tenant_id
    ).first()
    
    if not db_key:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    db.delete(db_key)
    db.commit()
    return None
