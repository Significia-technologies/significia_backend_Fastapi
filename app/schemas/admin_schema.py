from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class ClientProvisionRequest(BaseModel):
    company_name: str = Field(..., description="The name of the new client's company (tenant)")
    email: EmailStr = Field(..., description="The email address for the root owner of this tenant")
    password: str = Field(..., min_length=8, description="Temporary or initial password for the root owner")
