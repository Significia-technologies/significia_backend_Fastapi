import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base

class StorageConnector(Base):
    __tablename__ = "storage_connectors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True) # Optional back-reference
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="S3", nullable=False)  # S3, GCS, AZURE, LOCAL
    
    # Connection details
    bucket_name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    endpoint_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Encrypted credentials
    access_key_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    encrypted_secret_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Initialization status
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING, READY, FAILED
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
