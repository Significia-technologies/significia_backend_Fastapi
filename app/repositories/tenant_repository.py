import uuid
from sqlalchemy.orm import Session
from app.models.tenant import Tenant

class TenantRepository:
    def get_by_id(self, db: Session, tenant_id: uuid.UUID) -> Tenant:
        return db.query(Tenant).filter(Tenant.id == tenant_id).first()

    def create(self, db: Session, name: str) -> Tenant:
        db_tenant = Tenant(name=name)
        db.add(db_tenant)
        db.commit()
        db.refresh(db_tenant)
        return db_tenant
