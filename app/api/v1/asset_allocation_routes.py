"""
Asset Allocation Routes — Bridge Architecture
──────────────────────────────────────────────
Asset allocation endpoints now support Bridge-powered routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
import uuid

from app.api.deps import get_bridge_client
from app.services.bridge_client import BridgeClient
from app.schemas.asset_allocation import AssetAllocationCreate

router = APIRouter()


# ════════════════════════════════════════════════════════════════════
#  BRIDGE-POWERED ROUTES (no connector_id)
# ════════════════════════════════════════════════════════════════════

@router.post("/bridge/save", response_model=dict)
async def save_asset_allocation_bridge(
    payload: AssetAllocationCreate,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Save an asset allocation via the Bridge."""
    return await bridge.post("/asset-allocations", payload.model_dump())


@router.get("/bridge/allocations", response_model=list)
async def list_allocations_bridge(
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """List all asset allocations via the Bridge."""
    return await bridge.get("/asset-allocations")


@router.get("/bridge/allocation/{allocation_id}", response_model=dict)
async def get_allocation_bridge(
    allocation_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Get a specific allocation via the Bridge."""
    return await bridge.get(f"/asset-allocations/{allocation_id}")
