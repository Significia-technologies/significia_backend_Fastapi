from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.schemas.admin_schema import ClientProvisionRequest
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.models.user import User

class AdminService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.tenant_repo = TenantRepository()

    def provision_client(self, db: Session, request: ClientProvisionRequest) -> dict:
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
            password_hash=None, # Pure Bridge Auth: We don't store IA owner passwords in Master
            role="owner",
            status="active"
        )
        created_user = self.user_repo.create(db, user)
        
        return {
            "id": str(created_user.id),
            "email": created_user.email,
            "tenant_id": str(tenant.id),
            "tenant_name": tenant.name,
            "subdomain": tenant.subdomain,
            "bridge_registration_token": tenant.bridge_registration_token,
            "message": "Client provisioned successfully. They will set their password during Bridge setup."
        }
