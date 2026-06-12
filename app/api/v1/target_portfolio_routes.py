"""
Target Portfolio Routes — Bridge Proxy
───────────────────────────────────────
Proxies target portfolio requests to the tenant's Bridge.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_bridge_client, get_current_user, get_db
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
    export_basis: str = Query("objective"),
    objective: Optional[str] = Query(None),
    asset_classes: Optional[str] = Query(None),
    client_name: str = Query(""),
    client_code: str = Query(""),
    bridge: BridgeClient = Depends(get_bridge_client),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    params = {}
    if export_basis == "product" and asset_classes:
        params["asset_classes"] = asset_classes.split(",")
    else:
        params["objective"] = objective

    report_data = await bridge.get(
        f"/target-portfolio/{client_id}/{member_id}/report-data",
        params=params,
    )

    if not report_data.get("sections"):
        from fastapi import HTTPException
        filter_desc = f"objective '{objective}'" if export_basis == "objective" else "selected products"
        raise HTTPException(404, f"No active entries found for {filter_desc}.")

    ia_data = await bridge.get("/ia-master")

    # Resolve Logo Path
    logo_path = None
    ia_logo_key = ia_data.get("ia_logo_path")
    if ia_logo_key:
        try:
            from app.utils.file_utils import resolve_logo_to_local_path
            url_resp = await bridge.get("/storage/url", params={"key": ia_logo_key})
            signed_url = url_resp.get("url")
            if signed_url:
                logo_path = await resolve_logo_to_local_path(signed_url, db)
        except Exception:
            pass

    # Fetch asset allocation date if available
    allocation_date_str = None
    try:
        from datetime import datetime
        allocations = await bridge.get("/asset-allocations", params={"client_id": client_id})
        if allocations and isinstance(allocations, list):
            allocations.sort(
                key=lambda x: x.get("created_at") or "",
                reverse=True
            )
            latest_allocation = allocations[0]
            raw_date = latest_allocation.get("created_at")
            if raw_date:
                if "T" in raw_date:
                    dt_obj = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    allocation_date_str = dt_obj.strftime("%d %b %Y")
                else:
                    allocation_date_str = str(raw_date)[:10]
    except Exception:
        pass

    asset_classes_list = asset_classes.split(",") if asset_classes else None

    pdf_bytes = TargetPortfolioPDFGenerator.generate_report(
        report_data=report_data,
        client_name=client_name,
        client_code=client_code,
        ia_data=ia_data if isinstance(ia_data, dict) else None,
        logo_path=logo_path,
        export_basis=export_basis,
        asset_classes=asset_classes_list,
        allocation_date=allocation_date_str,
    )

    safe_client = "".join(c if c.isalnum() else "_" for c in client_code)
    safe_code = report_data.get("investor_code", "investor").replace("/", "_")
    if export_basis == "product":
        suffix = "Products"
    else:
        suffix = "".join(c if c.isalnum() else "_" for c in (objective or "Report"))
    filename = f"TargetPortfolio_{safe_client}_{safe_code}_{suffix}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/target-portfolio/{client_id}/report/pdf")
async def download_target_portfolio_client_report(
    client_id: str,
    client_name: str = Query(""),
    client_code: str = Query(""),
    bridge: BridgeClient = Depends(get_bridge_client),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    report_data = await bridge.get(
        f"/target-portfolio/{client_id}/report-data/investor-wise"
    )

    if not report_data.get("members"):
        from fastapi import HTTPException
        raise HTTPException(404, "No active target portfolio entries found for any family member.")

    ia_data = await bridge.get("/ia-master")

    # Resolve Logo Path
    logo_path = None
    ia_logo_key = ia_data.get("ia_logo_path")
    if ia_logo_key:
        try:
            from app.utils.file_utils import resolve_logo_to_local_path
            url_resp = await bridge.get("/storage/url", params={"key": ia_logo_key})
            signed_url = url_resp.get("url")
            if signed_url:
                logo_path = await resolve_logo_to_local_path(signed_url, db)
        except Exception:
            pass

    # Fetch asset allocation date if available
    allocation_date_str = None
    try:
        from datetime import datetime
        allocations = await bridge.get("/asset-allocations", params={"client_id": client_id})
        if allocations and isinstance(allocations, list):
            allocations.sort(
                key=lambda x: x.get("created_at") or "",
                reverse=True
            )
            latest_allocation = allocations[0]
            raw_date = latest_allocation.get("created_at")
            if raw_date:
                if "T" in raw_date:
                    dt_obj = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    allocation_date_str = dt_obj.strftime("%d %b %Y")
                else:
                    allocation_date_str = str(raw_date)[:10]
    except Exception:
        pass

    pdf_bytes = TargetPortfolioPDFGenerator.generate_report(
        report_data=report_data,
        client_name=client_name,
        client_code=client_code,
        ia_data=ia_data if isinstance(ia_data, dict) else None,
        logo_path=logo_path,
        export_basis="investor",
        allocation_date=allocation_date_str,
    )

    safe_client = "".join(c if c.isalnum() else "_" for c in client_code)
    filename = f"TargetPortfolio_{safe_client}_InvestorWise.pdf"

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
    db: Session = Depends(get_db),
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

    # Resolve Logo Path
    logo_path = None
    ia_logo_key = ia_data.get("ia_logo_path")
    if ia_logo_key:
        try:
            from app.utils.file_utils import resolve_logo_to_local_path
            url_resp = await bridge.get("/storage/url", params={"key": ia_logo_key})
            signed_url = url_resp.get("url")
            if signed_url:
                logo_path = await resolve_logo_to_local_path(signed_url, db)
        except Exception:
            pass

    # 4. Generate PDF report bytes
    pdf_bytes = AllocationTargetPDFGenerator.generate_report(
        allocation_data=latest_allocation,
        total_portfolio_size=total_portfolio_size,
        client_name=client_name,
        client_code=client_code,
        member_name=member_name,
        member_code=member_code,
        ia_data=ia_data if isinstance(ia_data, dict) else None,
        logo_path=logo_path,
    )

    safe_client = "".join(c if c.isalnum() else "_" for c in client_code)
    filename = f"TargetPortfolio_Allocation_Breakdown_{safe_client}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

