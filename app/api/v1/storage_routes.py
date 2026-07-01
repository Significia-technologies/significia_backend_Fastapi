"""
Storage Routes — File URL & Upload Proxy
─────────────────────────────────────────
Thin proxy to the Bridge storage service.
"""
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_bridge_client, get_current_user
from app.services.bridge_client import BridgeClient

router = APIRouter()


@router.get("/url")
async def get_file_url(
    key: str = Query(..., description="Storage key of the file"),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user: Any = Depends(get_current_user),
):
    """Get a pre-signed URL for a stored file."""
    return await bridge.get("/storage/url", params={"key": key})
