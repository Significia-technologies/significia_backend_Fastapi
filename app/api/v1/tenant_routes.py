from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_db, get_current_user, get_current_ia_owner, get_current_tenant
from app.services.tenant_service import TenantService
from app.schemas.tenant_schema import TenantPortalUpdate, TenantResponse
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter()
tenant_service = TenantService()

@router.get("/me", response_model=TenantResponse)
async def get_my_tenant(
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get the current tenant's profile."""
    return tenant

@router.patch("/me/portal", response_model=TenantResponse)
async def update_my_portal_settings(
    update_data: TenantPortalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ia_owner),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Update the current tenant's subdomain or custom domain.
    Only accessible to IA Owners.
    """
    # Ensure current_user belongs to current_tenant
    if current_user.tenant_id != current_tenant.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You are not authorized to manage this tenant"
        )
    
    return tenant_service.update_portal_settings(
        db=db, 
        tenant_id=current_tenant.id, 
        subdomain=update_data.subdomain, 
        custom_domain=update_data.custom_domain
    )
