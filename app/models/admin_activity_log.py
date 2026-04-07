import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TEXT
from app.database.base import Base
from app.core.timezone import get_now_ist

class AdminActivityLog(Base):
    __tablename__ = "admin_activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # The Admin who performed the action
    admin_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Metadata for quick viewing
    admin_email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    action: Mapped[str] = mapped_column(String(100), nullable=False) # e.g., "PROVISION_CLIENT", "CREATE_STAFF", "DEACTIVATE_STAFF"
    target_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., "tenant", "user", "ia_master"
    target_id: Mapped[str] = mapped_column(String(100), nullable=True)
    
    details: Mapped[str] = mapped_column(TEXT, nullable=True) # JSON or descriptive string
    
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_now_ist)

    # Relationships
    admin = relationship("User", foreign_keys=[admin_id])
