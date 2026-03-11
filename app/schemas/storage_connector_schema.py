from typing import Optional
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class StorageConnectorBase(BaseModel):
    name: str
    provider: str
    bucket_name: str
    region: Optional[str] = None
    endpoint_url: Optional[str] = None
    access_key_id: Optional[str] = None

class StorageConnectorCreate(StorageConnectorBase):
    secret_key: Optional[str] = None

class StorageConnectorUpdate(BaseModel):
    name: Optional[str] = None
    bucket_name: Optional[str] = None
    region: Optional[str] = None
    endpoint_url: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_key: Optional[str] = None
    is_active: Optional[bool] = None

class StorageConnectorResponse(StorageConnectorBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    verified_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
