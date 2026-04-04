from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.schemas.admin_schema import ClientProvisionRequest
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.repositories.ia_master_repository import IAMasterRepository
from app.models.user import User

class AdminService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.tenant_repo = TenantRepository()
        self.ia_repo = IAMasterRepository()

    def provision_client(self, db: Session, request: ClientProvisionRequest) -> dict:
        # 1. Check if email exists
        if self.user_repo.get_by_email(db, request.email):
            raise HTTPException(status_code=400, detail="Email already registered to an account")

        # 2. Create the new Tenant (Company) with billing info
        tenant = self.tenant_repo.create(
            db, 
            name=request.company_name,
            subdomain=request.subdomain,
            pricing_model=request.pricing_model,
            billing_mode=request.billing_mode,
            plan_expiry_date=request.plan_expiry_date,
            max_client_permit=request.max_client_permit
        )

        # 3. Create the IA Master record for registration info
        ia_data = {
            "tenant_id": tenant.id,
            "name_of_ia": tenant.name,
            "name_of_entity": tenant.name,
            "nature_of_entity": request.nature_of_entity,
            "ia_registration_number": request.registration_no,
            "date_of_registration_expiry": request.license_expiry_date,
            "registered_email_id": request.email,
            "is_renewal": request.is_renewal,
            "renewal_certificate_no": request.renewal_certificate_no,
            "renewal_expiry_date": request.renewal_expiry_date,
            "relationship_manager_id": request.relationship_manager_id,
            "date_of_birth": "1990-01-01", # Placeholder, IA will update in profile
            "bank_account_number": "", # Placeholder
            "bank_name": "",
            "bank_branch": "",
            "ifsc_code": ""
        }
        db_ia = self.ia_repo.create(db, ia_data)

        # 4. Create Contact Persons
        for cp in request.contact_persons:
            cp_data = {
                "ia_master_id": db_ia.id,
                **cp.dict()
            }
            self.ia_repo.create_contact_person(db, cp_data)

        # 5. Create the Root User (Owner) for this Tenant
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
            "message": "Client provisioned successfully with full registration and billing profile."
        }
