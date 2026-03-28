from sqlalchemy.orm import DeclarativeBase
import uuid

class Base(DeclarativeBase):
    """
    Base class for Master Orchestrator models (Tenants, Users, Connectors).
    """
    pass

class SiloBase(DeclarativeBase):
    """
    Base class for Tenant Silo models (IAMaster, Clients, Business logic).
    These models are managed separately by the ProvisionerService and do not
    participate in Master DB migrations.
    """
    pass
