"""
Target Portfolio Routes — Bridge Proxy
───────────────────────────────────────
Proxies target portfolio requests to the tenant's Bridge.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.api.deps import get_bridge_client, get_current_user
from app.services.bridge_client import BridgeClient
from app.utils.reports.target_portfolio_report import TargetPortfolioPDFGenerator

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


@router.get("/target-portfolio/{client_id}/{member_id}/report/pdf")
async def download_target_portfolio_report(
    client_id: str,
    member_id: str,
    objective: str = Query(...),
    client_name: str = Query(""),
    client_code: str = Query(""),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    report_data = await bridge.get(
        f"/target-portfolio/{client_id}/{member_id}/report-data",
        params={"objective": objective},
    )

    if not report_data.get("sections"):
        from fastapi import HTTPException
        raise HTTPException(404, f"No active entries found for objective '{objective}'.")

    ia_data = await bridge.get("/ia-master")

    pdf_bytes = TargetPortfolioPDFGenerator.generate_report(
        report_data=report_data,
        client_name=client_name,
        client_code=client_code,
        ia_data=ia_data if isinstance(ia_data, dict) else None,
    )

    safe_client = "".join(c if c.isalnum() else "_" for c in client_code)
    safe_code = report_data.get("investor_code", "investor").replace("/", "_")
    safe_obj = "".join(c if c.isalnum() else "_" for c in objective)
    filename = f"TargetPortfolio_{safe_client}_{safe_code}_{safe_obj}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/target-portfolio/{client_id}/{member_id}/allocation-target/pdf")
async def download_target_allocation_pdf(
    client_id: str,
    member_id: str,
    total_portfolio_size: float = Query(...),
    client_name: str = Query(""),
    client_code: str = Query(""),
    member_name: str = Query(""),
    member_code: str = Query(""),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    from app.utils.reports.allocation_target_report import AllocationTargetPDFGenerator
    from fastapi import HTTPException

    # 1. Fetch all asset allocations for this client from the Bridge
    allocations = await bridge.get("/asset-allocations", params={"client_id": client_id})
    if not allocations:
        raise HTTPException(status_code=404, detail="No asset allocation record found for this client. Please create one first.")

    # 2. Sort descending to get the latest
    try:
        allocations.sort(
            key=lambda x: x.get("created_at") or "",
            reverse=True
        )
    except Exception:
        pass
    latest_allocation = allocations[0]

    # 3. Fetch IA Master details for branding
    ia_data = await bridge.get("/ia-master")

    # 4. Generate PDF report bytes
    pdf_bytes = AllocationTargetPDFGenerator.generate_report(
        allocation_data=latest_allocation,
        total_portfolio_size=total_portfolio_size,
        client_name=client_name,
        client_code=client_code,
        member_name=member_name,
        member_code=member_code,
        ia_data=ia_data if isinstance(ia_data, dict) else None,
    )

    safe_client = "".join(c if c.isalnum() else "_" for c in client_code)
    filename = f"TargetPortfolio_Allocation_Breakdown_{safe_client}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

