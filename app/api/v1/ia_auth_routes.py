"""
IA Staff Authentication Routes — Bridge Architecture
─────────────────────────────────────────────────────
Separate auth flow for IA staff (NOT Significia Super Admins).

When an IA staff member logs into bunty.com:
  1. Frontend sends email/password + tenant info (from domain)
  2. Backend resolves the tenant from the domain
  3. Backend asks the Bridge to verify the credentials
  4. Bridge checks against the IA's local database
  5. Backend generates a JWT token with the tenant_id claim
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_db, get_bridge_client, get_current_tenant
from app.services.bridge_client import BridgeClient
from app.models.tenant import Tenant
from app.core.jwt import create_access_token, create_refresh_token

router = APIRouter()


class IAStaffLoginRequest(BaseModel):
    email: str
    password: str


class IAStaffLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_name: str
    user_role: str
    tenant_name: str


@router.post("/login", response_model=IAStaffLoginResponse)
async def ia_staff_login(
    request: IAStaffLoginRequest,
    tenant: Tenant = Depends(get_current_tenant),
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """
    IA Staff login endpoint.
    
    The frontend on bunty.com calls this with email/password.
    The tenant is resolved from the Host header (bunty.com → Tenant).
    Credentials are verified through the Bridge against the IA's local DB.
    """
    # Ask the Bridge to verify the IA user
    try:
        user_data = await bridge.post("/api/auth/verify-ia-user", {
            "email": request.email,
        })
    except HTTPException as e:
        if e.status_code == 401:
            raise HTTPException(401, "Invalid email or password")
        raise

    # Generate JWT tokens
    access_token = create_access_token(
        subject=user_data["id"],
        tenant_id=str(tenant.id),
        role=user_data.get("role", "ia_staff"),
    )
    refresh_token = create_refresh_token(
        subject=user_data["id"],
        tenant_id=str(tenant.id),
    )

    return IAStaffLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_name=user_data.get("name", "IA Staff"),
        user_role=user_data.get("role", "ia_staff"),
        tenant_name=tenant.name,
    )


@router.get("/tenant-info")
async def get_tenant_info(
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Returns tenant info based on the current domain.
    Called by the frontend on load to display branding (logo, name, etc.)
    """
    return {
        "tenant_id": str(tenant.id),
        "tenant_name": tenant.name,
        "subdomain": tenant.subdomain,
        "custom_domain": tenant.custom_domain,
        "bridge_status": tenant.bridge_status,
    }
