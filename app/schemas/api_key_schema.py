from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime

class ApiKeyBase(BaseModel):
    name: str
    allowed_domains: List[str] = []

class ApiKeyCreate(ApiKeyBase):
    pass

class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    allowed_domains: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ApiKeyResponse(ApiKeyBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ApiKeyCreateResponse(ApiKeyResponse):
    plain_key: str # Only returned once upon creation!
