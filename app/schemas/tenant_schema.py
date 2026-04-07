from pydantic import BaseModel, Field, validator
from typing import Optional
import re

class TenantPortalUpdate(BaseModel):
    subdomain: Optional[str] = Field(None, min_length=3, max_length=63)
    custom_domain: Optional[str] = Field(None, min_length=4, max_length=253)

    @validator("subdomain")
    def validate_subdomain(cls, v):
        if v is None:
            return v
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Subdomain can only contain lowercase letters, numbers, and hyphens")
        if v in ["www", "app", "api", "master", "admin", "significia"]:
            raise ValueError("This subdomain is reserved and cannot be used")
        return v

    @validator("custom_domain")
    def validate_custom_domain(cls, v):
        if v is None:
            return v
        # Basic domain validation: word.word
        if not re.match(r"^[a-z0-9-]+\.[a-z0-9.-]+$", v):
            raise ValueError("Invalid custom domain format")
        return v

import uuid

class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    subdomain: Optional[str]
    custom_domain: Optional[str]
    bridge_url: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
