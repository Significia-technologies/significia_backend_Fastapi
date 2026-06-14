from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
from app.api.deps import get_bridge_client
from app.services.bridge_client import BridgeClient

router = APIRouter()

@router.post("/bridge/save", response_model=dict)
async def save_existing_asset_allocation_bridge(
    payload: dict,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Save an existing asset allocation via the Bridge."""
    return await bridge.post("/existing-asset-allocations", payload)


@router.get("/bridge/allocations", response_model=list)
async def list_existing_allocations_bridge(
    client_id: Optional[str] = None,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """List all existing asset allocations via the Bridge, optionally filtered by client_id."""
    params = {"client_id": client_id} if client_id else None
    return await bridge.get("/existing-asset-allocations", params=params)


@router.get("/bridge/allocation/{allocation_id}", response_model=dict)
async def get_existing_allocation_bridge(
    allocation_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Get a specific existing allocation via the Bridge."""
    return await bridge.get(f"/existing-asset-allocations/{allocation_id}")
