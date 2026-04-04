from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date as date_type
from uuid import UUID

class ContactPersonBase(BaseModel):
    name: str
    designation: Optional[str] = None
    phone_number: str
    email: EmailStr
    address: Optional[str] = None

class ContactPersonCreate(ContactPersonBase):
    pass

class ClientProvisionRequest(BaseModel):
    company_name: str = Field(..., description="The name of the new client's company (tenant)")
    email: EmailStr = Field(..., description="The email address for the root owner of this tenant")
    subdomain: Optional[str] = Field(None, description="Optional subdomain (slug) for the tenant")
    
    # New registration fields
    nature_of_entity: str = "Individual"
    registration_no: str
    license_expiry_date: date_type
    
    # Renewal fields
    is_renewal: bool = False
    renewal_certificate_no: Optional[str] = None
    renewal_expiry_date: Optional[date_type] = None
    
    # RM mapping
    relationship_manager_id: Optional[UUID] = None
    
    # Contact persons
    contact_persons: List[ContactPersonCreate] = []
    
    # Billing fields
    pricing_model: str = "flat_fee"
    billing_mode: str = "yearly"
    plan_expiry_date: Optional[date_type] = None
    max_client_permit: int = 5

class ClientProvisionResponse(BaseModel):
    id: str
    email: str
    tenant_id: str
    tenant_name: str
    subdomain: Optional[str]
    bridge_registration_token: str
    message: str = "Client provisioned successfully"
