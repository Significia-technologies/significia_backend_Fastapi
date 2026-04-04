from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.deps import get_db, get_current_ia_owner, require_profile_completed
from app.schemas.admin_schema import StaffUserCreate, StaffUserOut, StaffUserUpdate
from app.services.admin_service import AdminService
from app.models.user import User

router = APIRouter()
admin_service = AdminService()

@router.get("/", response_model=List[StaffUserOut])
def list_team_members(
    db: Session = Depends(get_db),
    current_owner: User = Depends(get_current_ia_owner)
):
    """
    List all team members (Partners, Staff, Analysts) for the current IA's organization.
    """
    return admin_service.list_staff(db, current_owner.tenant_id)

@router.post("/", response_model=StaffUserOut, status_code=201)
def onboard_team_member(
    request_data: StaffUserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_owner: User = Depends(get_current_ia_owner),
    # Ensure profile is completed before onboarding others
    _ = Depends(require_profile_completed)
):
    """
    Onboard a new Partner or Staff member.
    The new member will be counted against the organization's 'Internal User' limit.
    """
    # 1. License Check (Internal Users only)
    tenant = current_owner.tenant
    current_usage = db.query(User).filter(
        User.tenant_id == tenant.id,
        User.role.in_(["owner", "partner", "ia_staff", "analyst", "staff"])
    ).count()

    if current_usage >= tenant.max_client_permit:
        raise HTTPException(
            status_code=403,
            detail=f"User limit reached ({tenant.max_client_permit}). Please upgrade your plan to onboard more team members."
        )

    # 2. Prevent IA Owners from creating Super Admins
    if request_data.role not in ["partner", "ia_staff", "analyst"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. You can only onboard Partners, Staff, or Analysts."
        )

    client_ip = request.client.host
    return admin_service.create_staff_user(db, current_owner, request_data.dict(), ip_address=client_ip)

@router.put("/{user_id}", response_model=StaffUserOut)
def update_team_member(
    user_id: UUID,
    request_data: StaffUserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_owner: User = Depends(get_current_ia_owner)
):
    """
    Update a team member's details or role.
    """
    # Ensure the user belongs to the same tenant
    target_user = db.query(User).filter(User.id == user_id, User.tenant_id == current_owner.tenant_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Team member not found in your organization.")

    client_ip = request.client.host
    return admin_service.update_staff_user(db, current_owner, str(user_id), request_data.dict(), ip_address=client_ip)

@router.delete("/{user_id}", status_code=204)
def remove_team_member(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_owner: User = Depends(get_current_ia_owner)
):
    """
    Deactivate a team member.
    """
    target_user = db.query(User).filter(User.id == user_id, User.tenant_id == current_owner.tenant_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Team member not found.")
    
    if target_user.id == current_owner.id:
        raise HTTPException(status_code=400, detail="You cannot remove yourself.")

    target_user.status = "inactive"
    db.commit()
    return None
