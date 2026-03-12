import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas.client_schema import ClientCreate, ClientUpdate
from app.models.ia_master import IAMaster
from app.models.client import ClientProfile
from app.core.security import get_password_hash

class ClientService:
    @staticmethod
    def _log_audit(db: Session, client_id: uuid.UUID, action: str, changes: Optional[dict] = None):
        from app.models.client import ClientAuditTrail
        audit = ClientAuditTrail(
            client_id=client_id,
            action_type=action,
            changes=changes
        )
        db.add(audit)

    @staticmethod
    def create_client(db: Session, client_in: ClientCreate) -> ClientProfile:
        # Check IA Master Limit
        ia_master = db.query(IAMaster).order_by(IAMaster.created_at.desc()).first()
        if not ia_master:
            raise ValueError("IA Master record must be created before adding clients.")
        
        if ia_master.current_client_count >= ia_master.max_client_permit:
            raise ValueError(f"Maximum client permit ({ia_master.max_client_permit}) reached.")
 
        # Check existing
        existing = db.query(ClientProfile).filter(
            (ClientProfile.email_normalized == client_in.email.lower()) | 
            (ClientProfile.pan_number == client_in.pan_number)
        ).first()

        if existing:
            if existing.deleted_at:
                # Reactivate soft-deleted client if same email/PAN?
                # For now just block as per standard logic, but could be handled.
                raise ValueError("A deactivated client with this email or PAN already exists.")
            raise ValueError("Client with this email or PAN already exists.")

        create_data = client_in.model_dump()
        raw_password = create_data.pop("password")
        
        db_client = ClientProfile(
            **create_data,
            password_hash=get_password_hash(raw_password),
            email_normalized=client_in.email.lower()
        )
        
        db.add(db_client)
        
        # Increment client count
        ia_master.current_client_count += 1
        
        db.commit()
        db.refresh(db_client)
        
        ClientService._log_audit(db, db_client.id, "CREATE")
        db.commit()
        
        return db_client

    @staticmethod
    def get_client(db: Session, client_id: uuid.UUID) -> Optional[ClientProfile]:
        return db.query(ClientProfile).filter(
            ClientProfile.id == client_id,
            ClientProfile.deleted_at == None
        ).first()

    @staticmethod
    def list_clients(db: Session) -> List[ClientProfile]:
        return db.query(ClientProfile).filter(ClientProfile.deleted_at == None).all()

    @staticmethod
    def update_client(db: Session, client_id: uuid.UUID, client_in: ClientUpdate) -> Optional[ClientProfile]:
        db_client = ClientService.get_client(db, client_id)
        if not db_client:
            return None
        
        update_data = client_in.model_dump(exclude_unset=True)
        changes = {}
        for key, value in update_data.items():
            old_val = getattr(db_client, key)
            if old_val != value:
                changes[key] = {"old": str(old_val), "new": str(value)}
                setattr(db_client, key, value)
            
        if changes:
            ClientService._log_audit(db, db_client.id, "UPDATE", changes)
            db.commit()
            db.refresh(db_client)
            
        return db_client

    @staticmethod
    def delete_client(db: Session, client_id: uuid.UUID) -> bool:
        db_client = ClientService.get_client(db, client_id)
        if not db_client:
            return False
            
        ia_master = db.query(IAMaster).order_by(IAMaster.created_at.desc()).first()
        if ia_master and ia_master.current_client_count > 0:
            ia_master.current_client_count -= 1
            
        # Soft delete
        db_client.is_active = False
        db_client.deleted_at = datetime.utcnow()
        
        ClientService._log_audit(db, db_client.id, "DELETE")
        db.commit()
        return True
