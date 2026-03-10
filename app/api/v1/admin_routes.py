from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_super_admin
from app.schemas.admin_schema import ClientProvisionRequest
from app.schemas.auth_schema import UserResponse
from app.services.admin_service import AdminService
from app.models.user import User

router = APIRouter()
admin_service = AdminService()

@router.post("/clients", response_model=UserResponse, status_code=201)
def provision_new_client(
    request: ClientProvisionRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_super_admin)
):
    """
    Super Admin endpoint to manually provision a new Client (Tenant)
    and their initial root Owner account.
    """
    return admin_service.provision_client(db, request)
