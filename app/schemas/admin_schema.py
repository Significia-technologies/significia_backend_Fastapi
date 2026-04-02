from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class ClientProvisionRequest(BaseModel):
    company_name: str = Field(..., description="The name of the new client's company (tenant)")
    email: EmailStr = Field(..., description="The email address for the root owner of this tenant")
    subdomain: Optional[str] = Field(None, description="Optional subdomain (slug) for the tenant")

class ClientProvisionResponse(BaseModel):
    id: str
    email: str
    tenant_id: str
    tenant_name: str
    subdomain: Optional[str]
    bridge_registration_token: str
    message: str = "Client provisioned successfully"
