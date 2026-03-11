import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models.ia_master import AuditTrail

class AuditTrailRepository:
    def create(self, db: Session, audit_data: dict) -> AuditTrail:
        db_audit = AuditTrail(**audit_data)
        db.add(db_audit)
        db.commit()
        db.refresh(db_audit)
        return db_audit

    def log_event(
        self, 
        db: Session, 
        action_type: str, 
        table_name: str, 
        record_id: str, 
        changes: Optional[str] = None, 
        user_ip: Optional[str] = None, 
        user_agent: Optional[str] = None
    ) -> AuditTrail:
        audit_data = {
            "action_type": action_type,
            "table_name": table_name,
            "record_id": record_id,
            "changes": changes,
            "user_ip": user_ip,
            "user_agent": user_agent
        }
        return self.create(db, audit_data)
