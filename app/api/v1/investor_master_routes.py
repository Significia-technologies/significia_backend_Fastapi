"""
Investor Master Routes — Bridge Proxy
──────────────────────────────────────
Proxies investor member requests to the tenant's Bridge.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_bridge_client, get_current_user
from app.services.bridge_client import BridgeClient

router = APIRouter()


@router.get("/investor-members/{client_id}")
async def list_investor_members(
    client_id: str,
    report_type: str = Query("full"),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    params = {"report_type": report_type}
    return await bridge.get(f"/investor-members/{client_id}", params=params)


@router.post("/investor-members/{client_id}")
async def create_investor_member(
    client_id: str,
    data: dict,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    return await bridge.post(f"/investor-members/{client_id}", data)


@router.patch("/investor-members/{client_id}/{member_id}/toggle")
async def toggle_investor_member(
    client_id: str,
    member_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    return await bridge.patch(f"/investor-members/{client_id}/{member_id}/toggle")
