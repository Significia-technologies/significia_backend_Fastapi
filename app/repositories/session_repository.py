import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user_session import UserSession
from app.models.refresh_token import RefreshToken

class SessionRepository:
    def create_session(self, db: Session, user_id: uuid.UUID, tenant_id: uuid.UUID, session_hash: str, device: Optional[str], ip_address: Optional[str], expires_at) -> UserSession:
        db_session = UserSession(
            user_id=user_id, 
            tenant_id=tenant_id, 
            session_token_hash=session_hash, 
            device=device, 
            ip_address=ip_address, 
            expires_at=expires_at
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session
        
    def create_refresh_token(self, db: Session, user_id: uuid.UUID, tenant_id: uuid.UUID, token_hash: str, expires_at) -> RefreshToken:
        db_token = RefreshToken(
            user_id=user_id, 
            tenant_id=tenant_id, 
            token_hash=token_hash, 
            expires_at=expires_at
        )
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token

    def get_refresh_token(self, db: Session, token_hash: str) -> Optional[RefreshToken]:
        return db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked == False).first()
