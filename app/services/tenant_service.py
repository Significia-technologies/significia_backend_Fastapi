import uuid
import logging
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.tenant import Tenant
from app.repositories.audit_trail_repository import AuditTrailRepository

logger = logging.getLogger("backend.tenant_service")

class TenantService:
    def __init__(self):
        self.audit_repo = AuditTrailRepository()

    def update_portal_settings(
        self, 
        db: Session, 
        tenant_id: uuid.UUID, 
        subdomain: Optional[str] = None, 
        custom_domain: Optional[str] = None
    ) -> Tenant:
        """
        Updates the subdomain or custom domain for a tenant.
        Ensures uniqueness across the platform.
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        changes = []

        # 1. Update Subdomain
        if subdomain is not None and subdomain != tenant.subdomain:
            # Check for uniqueness
            existing = db.query(Tenant).filter(Tenant.subdomain == subdomain, Tenant.id != tenant_id).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Subdomain '{subdomain}' is already taken"
                )
            old_val = tenant.subdomain
            tenant.subdomain = subdomain
            changes.append(f"Subdomain: {old_val} -> {subdomain}")

        # 2. Update Custom Domain
        if custom_domain is not None and custom_domain != tenant.custom_domain:
            # Check for uniqueness
            existing = db.query(Tenant).filter(Tenant.custom_domain == custom_domain, Tenant.id != tenant_id).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Custom domain '{custom_domain}' is already registered by another IA"
                )
            old_val = tenant.custom_domain
            tenant.custom_domain = custom_domain
            changes.append(f"Custom Domain: {old_val} -> {custom_domain}")

        if changes:
            db.commit()
            db.refresh(tenant)
            self.audit_repo.log_event(
                db, "UPDATE", "tenants", str(tenant.id), 
                changes="; ".join(changes)
            )
            logger.info(f"✅ Portal settings updated for tenant {tenant.name}: {'; '.join(changes)}")

        return tenant

    def get_tenant_by_id(self, db: Session, tenant_id: uuid.UUID) -> Optional[Tenant]:
        return db.query(Tenant).filter(Tenant.id == tenant_id).first()
