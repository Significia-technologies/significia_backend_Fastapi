from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.schemas.admin_schema import ClientProvisionRequest
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.models.user import User
from app.core.security import get_password_hash

class AdminService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.tenant_repo = TenantRepository()

    def provision_client(self, db: Session, request: ClientProvisionRequest) -> User:
        # Check if email exists
        if self.user_repo.get_by_email(db, request.email):
            raise HTTPException(status_code=400, detail="Email already registered to an account")

        # Create the new Tenant (Company)
        tenant = self.tenant_repo.create(db, name=request.company_name)

        # Create the Root User (Owner) for this Tenant
        user = User(
            tenant_id=tenant.id,
            email=request.email,
            email_normalized=request.email.lower(),
            password_hash=get_password_hash(request.password),
            role="owner", # Provisioned clients get the owner role of their own tenant
            status="active"
        )
        return self.user_repo.create(db, user)
