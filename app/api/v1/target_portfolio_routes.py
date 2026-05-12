"""
Target Portfolio Routes — Bridge Proxy
───────────────────────────────────────
Proxies target portfolio requests to the tenant's Bridge.
"""
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_bridge_client, get_current_user
from app.services.bridge_client import BridgeClient

router = APIRouter()


@router.get("/target-portfolio/{client_id}/{member_id}")
async def list_target_portfolio(
    client_id: str,
    member_id: str,
    asset_class: str = Query("shares"),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    return await bridge.get(
        f"/target-portfolio/{client_id}/{member_id}",
        params={"asset_class": asset_class},
    )


@router.get("/target-portfolio/{client_id}/{member_id}/products")
async def list_available_products(
    client_id: str,
    member_id: str,
    asset_class: str = Query("shares"),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    return await bridge.get(
        f"/target-portfolio/{client_id}/{member_id}/products",
        params={"asset_class": asset_class},
    )


@router.post("/target-portfolio/{client_id}/{member_id}")
async def create_target_portfolio_entry(
    client_id: str,
    member_id: str,
    data: dict,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    return await bridge.post(f"/target-portfolio/{client_id}/{member_id}", data)


@router.patch("/target-portfolio/{client_id}/{member_id}/{entry_id}/toggle")
async def toggle_target_portfolio_entry(
    client_id: str,
    member_id: str,
    entry_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    return await bridge.patch(
        f"/target-portfolio/{client_id}/{member_id}/{entry_id}/toggle"
    )
