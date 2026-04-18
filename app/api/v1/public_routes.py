from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import httpx

from app.api.deps import get_db
from app.models.tenant import Tenant

router = APIRouter()

@router.get("/branding")
async def get_tenant_branding(
    request: Request,
    db: Session = Depends(get_db),
    x_tenant_slug: Optional[str] = Header(None, alias="X-Tenant-Slug"),
    host: Optional[str] = Header(None)
):
    """
    Public endpoint to fetch tenant branding information.
    Used by the login page and dashboard to show the correct logo/name.
    Does NOT require authentication.
    """
    # 1. Resolve Tenant Slug
    tenant = None
    
    # Priority 1: X-Tenant-Slug header (set by simulator or mobile apps)
    if x_tenant_slug:
        tenant = db.query(Tenant).filter(Tenant.subdomain == x_tenant_slug).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
    # Priority 2: Host header (Subdomain detection)
    if not tenant and host:
        clean_host = host.split(':')[0].lower()
        root_domains = ["localhost", "127.0.0.1", "significia.com", "www.significia.com", "app.significia.com", "api.significia.com"]
        
        if clean_host not in root_domains:
            # Check if it's a subdomain of significia.com or localhost
            is_subdomain = False
            for root in ["significia.com", "localhost"]:
                if clean_host.endswith(f".{root}"):
                    is_subdomain = True
                    slug = clean_host.split(f".{root}")[0]
                    
                    # Block "master" being used as a subdomain
                    if slug == "master":
                         raise HTTPException(status_code=404, detail="Portal not available on this subdomain")
                         
                    tenant = db.query(Tenant).filter(Tenant.subdomain == slug).first()
                    break
            
            # If it was a subdomain but no tenant was found in DB
            if is_subdomain and not tenant:
                raise HTTPException(status_code=404, detail="Tenant not found")
        else:
            # Explicitly "master" if on root domains
            tenant = db.query(Tenant).filter(Tenant.subdomain == "master").first()

    # Final Check: If still no tenant resolved (e.g. unknown domain)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant context could not be resolved")


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
