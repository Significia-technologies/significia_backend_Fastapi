"""
Client Routes — Bridge Architecture
─────────────────────────────────────
All client data operations now go through the Bridge.
No direct database connections are made from this backend.
"""
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api.deps import get_bridge_client, get_current_tenant, get_db, get_current_user
from app.services.bridge_client import BridgeClient
from app.models.tenant import Tenant
from app.schemas.client_schema import ClientCreate, ClientUpdate, ClientResponse, ClientDocumentResponse
from app.utils.reports.client_blank_form import generate_client_blank_form
from app.utils.pdf_generator import ClientPDFGenerator

# Legacy imports removed as Bridge Architecture is fully enforced

router = APIRouter()


# ════════════════════════════════════════════════════════════════════
#  BRIDGE-POWERED ROUTES (new — no connector_id needed)
# ════════════════════════════════════════════════════════════════════

@router.post("/clients", response_model=dict)
async def create_client_bridge(
    client_in: ClientCreate,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Create a new client via the Bridge (enforces client limit on Bridge side)."""
    try:
        data = client_in.model_dump()
        # Hash the password before sending — Bridge stores the hash
        from app.core.security import get_password_hash
        raw_password = data.pop("password")
        data["password_hash"] = get_password_hash(raw_password)
        data["email_normalized"] = data["email"].lower()

        result = await bridge.post("/clients", data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clients", response_model=dict)
async def list_clients_bridge(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """List all clients via the Bridge."""
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    return await bridge.get("/clients", params=params)


@router.get("/clients/{client_id}", response_model=dict)
async def get_client_bridge(
    client_id: uuid.UUID,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Get a single client via the Bridge."""
    return await bridge.get(f"/clients/{client_id}")


@router.get("/clients/pan/{pan}", response_model=dict)
async def get_client_by_pan_bridge(
    pan: str,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Get client by PAN via the Bridge."""
    result = await bridge.get("/clients", params={"search": pan})
    clients = result.get("clients", [])
    for c in clients:
        if c.get("pan_number", "").upper() == pan.upper():
            return c
    raise HTTPException(status_code=404, detail="Client not found")


@router.get("/clients/code/{code}", response_model=dict)
async def get_client_by_code_bridge(
    code: str,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Get client by client code via the Bridge."""
    result = await bridge.get("/clients", params={"search": code})
    clients = result.get("clients", [])
    for c in clients:
        if c.get("client_code", "").upper() == code.upper():
            return c
    raise HTTPException(status_code=404, detail="Client not found")


@router.put("/clients/{client_id}", response_model=dict)
async def update_client_bridge(
    client_id: uuid.UUID,
    client_in: ClientUpdate,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Update a client via the Bridge."""
    update_data = client_in.model_dump(exclude_unset=True)
    return await bridge.patch(f"/clients/{client_id}", update_data)


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client_bridge(
    client_id: uuid.UUID,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Soft-delete a client via the Bridge."""
    await bridge.delete(f"/clients/{client_id}")
    return None


@router.post("/clients/{client_id}/upload-document", response_model=dict)
async def upload_client_document_bridge(
    client_id: uuid.UUID,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Upload a document for a client via the Bridge (stored in IA's own bucket)."""
    file_bytes = await file.read()
    result = await bridge.upload_file(
        f"/api/storage/upload",
        file_bytes=file_bytes,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
    )
    return result


@router.get("/billing/client-count", response_model=dict)
async def get_client_count_bridge(
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Get client count (billing metric) from the Bridge."""
    return await bridge.get("/billing/client-count")



