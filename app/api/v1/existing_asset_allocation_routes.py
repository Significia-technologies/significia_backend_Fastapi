from fastapi import APIRouter, Depends, HTTPException, Request, Response
from typing import Optional
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_bridge_client
from app.services.bridge_client import BridgeClient
from app.utils.reports.asset_allocation_report import AssetAllocationReportUtils

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


@router.get("/bridge/comparisons", response_model=list)
async def list_allocation_comparisons_bridge(
    client_id: Optional[str] = None,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """List all saved allocation comparisons via the Bridge, optionally filtered by client_id."""
    params = {"client_id": client_id} if client_id else None
    return await bridge.get("/allocation-comparisons", params=params)


@router.post("/bridge/compare/save", response_model=dict)
async def save_allocation_comparison_bridge(
    payload: dict,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Save a new allocation comparison via the Bridge."""
    return await bridge.post("/allocation-comparisons", payload)


@router.get("/bridge/allocation/{allocation_id}", response_model=dict)
async def get_existing_allocation_bridge(
    allocation_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Get a specific existing allocation via the Bridge."""
    return await bridge.get(f"/existing-asset-allocations/{allocation_id}")


@router.patch("/bridge/allocation/{allocation_id}", response_model=dict)
async def update_existing_allocation_bridge(
    allocation_id: str,
    payload: dict,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Update a specific existing asset allocation (useful for drafts) via the Bridge."""
    return await bridge.patch(f"/existing-asset-allocations/{allocation_id}", payload)


@router.get("/bridge/blank-form/pdf")
async def download_blank_form_pdf(
    bridge: BridgeClient = Depends(get_bridge_client),
    db: Session = Depends(get_db)
):
    """Generate and download a blank existing asset allocation form."""
    try:
        # 1. Fetch IA Master info from Bridge for branding
        ia_data = await bridge.get("/ia-master")
        
        # IA branding details
        ia_name = ia_data.get("name_of_ia") or "____________________________"
        ia_entity = ia_data.get("entity_name") or "____________________________"
        ia_reg_no = ia_data.get("registration_no") or "________________"
        ia_logo_key = ia_data.get("ia_logo_path")
        
        # 2. Resolve Logo from Bridge storage
        logo_path = None
        if ia_logo_key:
            try:
                from app.utils.file_utils import resolve_logo_to_local_path
                url_resp = await bridge.get("/storage/url", params={"key": ia_logo_key})
                signed_url = url_resp.get("url")
                if signed_url:
                    logo_path = await resolve_logo_to_local_path(signed_url, db)
            except: pass

        # 3. Create mock IA object (since we don't have direct DB access to IAMaster)
        class MockIA: pass
        ia = MockIA()
        ia.name_of_ia = ia_name
        ia.name_of_entity = ia_entity
        ia.ia_registration_number = ia_reg_no
        ia.ia_reg_no = ia_reg_no # Support multiple attribute names

        # 4. Generate PDF
        pdf_buffer = AssetAllocationReportUtils.generate_existing_blank_pdf(ia, ia_logo_path=logo_path)
        
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=Existing_Asset_Allocation_Blank_Form.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate blank form: {str(e)}")


@router.get("/bridge/allocation/compare/pdf")
async def download_comparison_pdf(
    existing_id: str,
    target_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    db: Session = Depends(get_db)
):
    """Generate and download a comparative asset allocation report PDF."""
    try:
        # 1. Fetch Existing Allocation details from Bridge
        existing_data = await bridge.get(f"/existing-asset-allocations/{existing_id}")
        if not existing_data:
            raise HTTPException(status_code=404, detail="Existing Asset Allocation not found")
        
        # 2. Fetch Target Allocation details from Bridge
        target_data = await bridge.get(f"/asset-allocations/{target_id}")
        if not target_data:
            raise HTTPException(status_code=404, detail="Target Asset Allocation not found")

        # 3. Fetch IA Master info from Bridge for branding
        ia_data = await bridge.get("/ia-master")
        
        # IA branding details
        ia_name = ia_data.get("name_of_ia") or "____________________________"
        ia_entity = ia_data.get("entity_name") or "____________________________"
        ia_reg_no = ia_data.get("registration_no") or "________________"
        ia_logo_key = ia_data.get("ia_logo_path")
        
        # 4. Resolve Logo from Bridge storage
        logo_path = None
        if ia_logo_key:
            try:
                from app.utils.file_utils import resolve_logo_to_local_path
                url_resp = await bridge.get("/storage/url", params={"key": ia_logo_key})
                signed_url = url_resp.get("url")
                if signed_url:
                    logo_path = await resolve_logo_to_local_path(signed_url, db)
            except: pass

        # 5. Create mock IA object
        class MockIA: pass
        ia = MockIA()
        ia.name_of_ia = ia_name
        ia.name_of_entity = ia_entity
        ia.ia_registration_number = ia_reg_no
        ia.ia_reg_no = ia_reg_no

        # 6. Generate PDF
        pdf_buffer = AssetAllocationReportUtils.generate_comparison_pdf(
            existing_data, target_data, ia, ia_logo_path=logo_path
        )
        
        client_code = existing_data.get("client_code") or target_data.get("client_code") or "Report"
        filename = f"Allocation_Comparison_{client_code.upper()}.pdf"

        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate comparison report: {str(e)}")


@router.get("/bridge/allocation/{allocation_id}/pdf")
async def download_existing_allocation_pdf(
    allocation_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    db: Session = Depends(get_db)
):
    """Generate and download a specific existing asset allocation report PDF."""
    try:
        # 1. Fetch Existing Allocation details from Bridge
        allocation_data = await bridge.get(f"/existing-asset-allocations/{allocation_id}")
        if not allocation_data:
            raise HTTPException(status_code=404, detail="Existing Asset Allocation not found")
        
        # 2. Fetch IA Master info from Bridge for branding
        ia_data = await bridge.get("/ia-master")
        
        # IA branding details
        ia_name = ia_data.get("name_of_ia") or "____________________________"
        ia_entity = ia_data.get("entity_name") or "____________________________"
        ia_reg_no = ia_data.get("registration_no") or "________________"
        ia_logo_key = ia_data.get("ia_logo_path")
        
        # 3. Resolve Logo from Bridge storage
        logo_path = None
        if ia_logo_key:
            try:
                from app.utils.file_utils import resolve_logo_to_local_path
                url_resp = await bridge.get("/storage/url", params={"key": ia_logo_key})
                signed_url = url_resp.get("url")
                if signed_url:
                    logo_path = await resolve_logo_to_local_path(signed_url, db)
            except: pass

        # 4. Create mock IA object (since we don't have direct DB access to IAMaster)
        class MockIA: pass
        ia = MockIA()
        ia.name_of_ia = ia_name
        ia.name_of_entity = ia_entity
        ia.ia_registration_number = ia_reg_no
        ia.ia_reg_no = ia_reg_no # Support multiple attribute names

        # 5. Generate PDF
        pdf_buffer = AssetAllocationReportUtils.generate_existing_pdf(allocation_data, ia, ia_logo_path=logo_path)
        
        client_code = allocation_data.get("client_code") or "Report"
        filename = f"Existing_Asset_Allocation_{client_code.upper()}.pdf"

        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate existing asset allocation report: {str(e)}")



