from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import httpx

from app.api.deps import get_db
from app.models.tenant import Tenant

router = APIRouter()

@router.get("/branding")
async def get_tenant_branding(
    db: Session = Depends(get_db),
    x_tenant_slug: Optional[str] = Header(None, alias="X-Tenant-Slug")
):
    """
    Public endpoint to fetch tenant branding information.
    Used by the login page and dashboard to show the correct logo/name.
    Does NOT require authentication.
    """
    # 1. Resolve Tenant Slug
    # In production, we would use request.url.hostname to map custom domains.
    # For now, we rely on the header (which is set by the simulator).
    slug = x_tenant_slug or "master"
    
    tenant = db.query(Tenant).filter(Tenant.subdomain == slug).first()
    if not tenant:
        # Fallback to master if tenant not found
        tenant = db.query(Tenant).filter(Tenant.subdomain == "master").first()
    
    if not tenant:
        return {
            "name": "Significia",
            "is_master": True,
            "logo_type": "significia",
            "logo_url": "/favicon-32x32.png"
        }

    # 2. Branding Logic
    branding = {
        "name": "Significia" if tenant.subdomain == "master" else tenant.name,
        "is_master": tenant.subdomain == "master",
        "logo_type": "shield", 
        "logo_url": None
    }

    if (tenant.subdomain == "master"):
        branding["logo_type"] = "significia"
        branding["logo_url"] = "/logo.png"
    else:
        # Default subtenant branding
        branding["logo_type"] = "shield"
        
    return branding
