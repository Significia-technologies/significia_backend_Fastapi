from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import httpx
import logging

from app.api.deps import get_db
from app.models.tenant import Tenant

logger = logging.getLogger("significia.public")

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
    
    Returns brand_color, portal_title, portal_description, and favicon_url
    for white-labeled IA portals.
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
            
            # If not a subdomain, check if it matches a custom domain
            if not is_subdomain and not tenant:
                tenant = db.query(Tenant).filter(Tenant.custom_domain == clean_host).first()

            # If it was a subdomain but no tenant was found in DB
            if is_subdomain and not tenant:
                raise HTTPException(status_code=404, detail="Tenant not found")
        else:
            # Explicitly "master" if on root domains
            tenant = db.query(Tenant).filter(Tenant.subdomain == "master").first()

    # Final Check: If still no tenant resolved (e.g. unknown domain)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant context could not be resolved")


    # 2. Base Branding Logic
    branding = {
        "name": "Significia" if tenant.subdomain == "master" else tenant.name,
        "is_master": tenant.subdomain == "master",
        "logo_type": "shield", 
        "logo_url": None,
        "brand_color": None,
        "brand_background_color_light": None,
        "brand_background_color_dark": None,
        "portal_title": None,
        "portal_description": None,
        "favicon_url": None,
    }

    if (tenant.subdomain == "master"):
        branding["logo_type"] = "significia"
        branding["logo_url"] = "/logo.png"
    else:
        # 3. For IA tenants, fetch branding from their Bridge silo
        branding["logo_type"] = "shield"
        
        if tenant.bridge_url and tenant.bridge_api_secret and tenant.bridge_status == "ACTIVE":
            try:
                bridge_base = f"{tenant.bridge_url.rstrip('/')}/api/v1/bridge"
                headers = {
                    "Authorization": f"Bearer {tenant.bridge_api_secret}",
                    "Content-Type": "application/json",
                }
                
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{bridge_base}/ia-master", headers=headers)
                    
                if resp.status_code == 200:
                    ia_data = resp.json()
                    
                    # Logo
                    if ia_data.get("ia_logo_path"):
                        storage_base = bridge_base.split("/api/v1/bridge")[0] + "/api/v1/bridge/storage"
                        logo_path = ia_data["ia_logo_path"]
                        if not logo_path.startswith("http"):
                            logo_path = f"{storage_base}/{logo_path}"
                        branding["logo_type"] = "custom"
                        branding["logo_url"] = logo_path
                    
                    # Favicon
                    if ia_data.get("favicon_path"):
                        storage_base = bridge_base.split("/api/v1/bridge")[0] + "/api/v1/bridge/storage"
                        fav_path = ia_data["favicon_path"]
                        if not fav_path.startswith("http"):
                            fav_path = f"{storage_base}/{fav_path}"
                        branding["favicon_url"] = fav_path
                    
                    # Brand color
                    if ia_data.get("brand_color"):
                        branding["brand_color"] = ia_data["brand_color"]
                    
                    # Background colors (light/dark mode)
                    if ia_data.get("brand_background_color_light"):
                        branding["brand_background_color_light"] = ia_data["brand_background_color_light"]
                    if ia_data.get("brand_background_color_dark"):
                        branding["brand_background_color_dark"] = ia_data["brand_background_color_dark"]
                    
                    # Portal meta
                    if ia_data.get("portal_title"):
                        branding["portal_title"] = ia_data["portal_title"]
                    if ia_data.get("portal_description"):
                        branding["portal_description"] = ia_data["portal_description"]
                else:
                    logger.warning(f"Bridge returned {resp.status_code} for tenant {tenant.name}")
                        
            except Exception as e:
                logger.warning(f"Failed to fetch branding from Bridge for tenant {tenant.name}: {e}")
                # Graceful fallback — return default branding
        
    return branding
