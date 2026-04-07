from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_super_admin
from app.schemas.admin_schema import (
    ClientProvisionRequest, ClientProvisionResponse,
    StaffUserCreate, StaffUserUpdate, StaffUserOut,
    AdminActivityLogOut
)
from app.services.admin_service import AdminService
from app.models.user import User

router = APIRouter()
admin_service = AdminService()

@router.post("/clients", response_model=ClientProvisionResponse, status_code=201)
def provision_new_client(
    request: ClientProvisionRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_super_admin)
):
    """
    Super Admin endpoint to manually provision a new Client (Tenant)
    and their initial root Owner account.
    """
    result = admin_service.provision_client(db, request)
    admin_service.log_activity(
        db, current_admin, "PROVISION_CLIENT", "tenant", 
        result["tenant_id"], f"Provisioned client: {result['tenant_name']}"
    )
    return result

# --- Staff Management ---

@router.get("/staff", response_model=list[StaffUserOut])
def list_staff(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_super_admin)
):
    return admin_service.list_staff(db, current_admin.tenant_id)

@router.post("/staff", response_model=StaffUserOut, status_code=201)
def create_staff(
    request: StaffUserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_super_admin)
):
    return admin_service.create_staff_user(db, current_admin, request.dict())

@router.put("/staff/{user_id}", response_model=StaffUserOut)
def update_staff(
    user_id: str,
    request: StaffUserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_super_admin)
):
    return admin_service.update_staff_user(db, current_admin, user_id, request.dict())

# --- Audit Logs ---

@router.get("/logs", response_model=list[AdminActivityLogOut])
def list_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_super_admin)
):
    return admin_service.get_logs(db, limit)
    
from pydantic import BaseModel

class BridgeInitializeRequest(BaseModel):
    password: str

@router.post("/bridge-initialize/{tenant_id}")
async def initialize_bridge(
    tenant_id: str,
    request: BridgeInitializeRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_super_admin),
):
    """
    Trigger database initialization on the IA's local Bridge.
    This tells the Bridge to create the significia_core schema and all tables.
    """
    import httpx
    import uuid as uuid_lib
    from app.models.tenant import Tenant
    from app.models.user import User
    
    print(f"[ADMIN DEBUG] Requested initialization for tenant_id: {tenant_id}")
    
    tenant = db.query(Tenant).filter(Tenant.id == uuid_lib.UUID(tenant_id)).first()
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    # Fetch the IA Owner from the Master DB to sync to the Bridge
    owner = db.query(User).filter(User.tenant_id == tenant.id, User.role == "owner").first()
    owner_data = None
    if owner:
        owner_data = {
            "email": owner.email, 
            "name": tenant.name,
            # We send the password plain-text over the secure Bridge connection
            # The Bridge will hash it locally and never send it back.
            "password": request.password 
        }
        print(f"[ADMIN DEBUG] Syncing owner: {owner.email} (Pushing credential for local hashing)")
    
    if not tenant.bridge_url:
        raise HTTPException(400, "Bridge URL is not configured. Is the Bridge online?")

    # Call the Bridge's local endpoint
    try:
        # Increase timeout for initialization as it does heavy DB work
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{tenant.bridge_url}/api/v1/bridge/initialize",
                headers={"Authorization": f"Bearer {tenant.bridge_api_secret}"},
                json={"owner_data": owner_data}
            )
            
            if response.status_code != 200:
                print(f"[ADMIN DEBUG] Bridge error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Bridge reported error: {response.text}"
                )
            
            return response.json()
    except httpx.RequestError as e:
        print(f"[ADMIN DEBUG] Request failed: {str(e)}")
        raise HTTPException(
            status_code=502, 
            detail=f"Could not reach the Bridge at {tenant.bridge_url}. Is it online? Error: {str(e)}"
        )
