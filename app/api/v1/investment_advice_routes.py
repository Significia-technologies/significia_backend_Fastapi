"""
Investment Advice Note Routes — Bridge Proxy
─────────────────────────────────────────────
Proxies investment advice note requests to the tenant's Bridge.
Follows the same pattern as target_portfolio_routes.py.
"""
from fastapi import APIRouter, Depends, Query, Body
from fastapi.responses import Response
from typing import Optional
from sqlalchemy.orm import Session

from app.api.deps import get_bridge_client, get_current_user, get_db
from app.services.bridge_client import BridgeClient

router = APIRouter()


# ── List all advice notes across all clients ──────────────────────
@router.get("/investment-advice-notes")
async def list_all_investment_advice_notes(
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    """List all investment advice notes across all clients."""
    return await bridge.get("/investment-advice-notes")


# ── List all advice notes for a client ────────────────────────────
@router.get("/investment-advice-notes/{client_id}")
async def list_investment_advice_notes(
    client_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    """List all investment advice notes for a client."""
    return await bridge.get(f"/investment-advice-notes/{client_id}")


# ── Create a new advice note draft ────────────────────────────────
@router.post("/investment-advice-notes/{client_id}")
async def create_investment_advice_note(
    client_id: str,
    data: dict,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    """Create a new investment advice note draft for a client."""
    return await bridge.post(f"/investment-advice-notes/{client_id}", data)


# ── Get full details of a specific advice note ────────────────────
@router.get("/investment-advice-note/{note_id}")
async def get_investment_advice_note(
    note_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    """Get full details of a specific advice note including recommendations."""
    return await bridge.get(f"/investment-advice-note/{note_id}")


# ── Update an unlocked advice note ────────────────────────────────
@router.patch("/investment-advice-note/{note_id}")
async def update_investment_advice_note(
    note_id: str,
    data: dict,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    """Update an unlocked investment advice note."""
    return await bridge.patch(f"/investment-advice-note/{note_id}", data)


# ── Lock an advice note (SEBI delivery compliance) ───────────────
@router.post("/investment-advice-note/{note_id}/lock")
async def lock_investment_advice_note(
    note_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    """Lock an advice note after delivery. No further edits allowed."""
    return await bridge.post(f"/investment-advice-note/{note_id}/lock")


# ── Add a product recommendation ─────────────────────────────────
@router.post("/investment-advice-note/{note_id}/recommendations")
async def add_recommendation(
    note_id: str,
    data: dict,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    """Add a product recommendation to an unlocked advice note."""
    return await bridge.post(f"/investment-advice-note/{note_id}/recommendations", data)


# ── Remove a product recommendation ──────────────────────────────
@router.delete("/investment-advice-note/{note_id}/recommendations/{rec_id}")
async def delete_recommendation(
    note_id: str,
    rec_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    """Remove a product recommendation from an unlocked advice note."""
    return await bridge.delete(f"/investment-advice-note/{note_id}/recommendations/{rec_id}")


# ── Update execution actions/taken status on recommendations ──────
@router.patch("/investment-advice-note/{note_id}/recommendations/action-taken")
async def update_recommendations_action_taken(
    note_id: str,
    data: list = Body(...),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    """Update action taken status on recommendations for an advice note."""
    return await bridge.patch(f"/investment-advice-note/{note_id}/recommendations/action-taken", data)


# ── Get next serial number (utility) ─────────────────────────────
@router.get("/investment-advice-note/{note_id}/next-serial")
async def get_next_serial(
    note_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    """Get the next advice note serial number."""
    return await bridge.get(f"/investment-advice-note/{note_id}/next-serial")


# ── Download advice note as PDF ───────────────────────────────────
@router.get("/investment-advice-note/{note_id}/export/pdf")
async def download_advice_note_pdf(
    note_id: str,
    validity_type: str = Query("all", description="Filter recommendations: all, valid, expired"),
    export_type: str = Query("full", description="Export type: full, execution_log"),
    bridge: BridgeClient = Depends(get_bridge_client),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate and download the Investment Advice Note as a PDF."""
    from fastapi import HTTPException
    from app.utils.reports.investment_advice_report import InvestmentAdviceNotePDF
    from datetime import datetime, date, timedelta
    import re

    # 1. Fetch the full note data (includes client_snapshot + recommendations)
    note_data = await bridge.get(f"/investment-advice-note/{note_id}")
    if not note_data or not isinstance(note_data, dict):
        raise HTTPException(404, "Advice note not found.")

    # Filter recommendations by validity
    recommendations = note_data.get("recommendations", [])
    if validity_type in ("valid", "expired"):
        filtered_recs = []
        default_days = note_data.get("advice_validity_days", 60)
        issue_date_str = note_data.get("date_of_issue")
        
        for rec in recommendations:
            is_valid = True
            try:
                # parse issue date
                issue_date_str_split = issue_date_str.split('T')[0]
                issue_date = datetime.strptime(issue_date_str_split, "%Y-%m-%d").date()
                
                validity_text = rec.get("advice_validity_text")
                days = default_days or 60
                if validity_text:
                    match = re.search(r'(\d+)\s*Day', validity_text, re.IGNORECASE)
                    if match:
                        days = int(match.group(1))
                    elif "immediate" in validity_text.lower():
                        days = 1
                        
                expiry_date = issue_date + timedelta(days=days)
                today = date.today()
                is_valid = expiry_date >= today
            except Exception:
                is_valid = True
            
            if (validity_type == "valid" and is_valid) or (validity_type == "expired" and not is_valid):
                filtered_recs.append(rec)
        note_data["recommendations"] = filtered_recs

    # 2. Fetch IA master data for header/footer branding
    ia_data = await bridge.get("/ia-master")
    ia_dict = ia_data if isinstance(ia_data, dict) else None

    # Resolve Logo Path
    logo_path = None
    ia_logo_key = ia_dict.get("ia_logo_path") if ia_dict else None
    if ia_logo_key:
        try:
            from app.utils.file_utils import resolve_logo_to_local_path
            url_resp = await bridge.get("/storage/url", params={"key": ia_logo_key})
            signed_url = url_resp.get("url")
            if signed_url:
                logo_path = await resolve_logo_to_local_path(signed_url, db)
        except Exception:
            pass

    # 3. Generate PDF
    pdf_bytes = InvestmentAdviceNotePDF.generate_pdf(
        note_data=note_data,
        ia_data=ia_dict,
        logo_path=logo_path,
        export_type=export_type,
    )

    # 4. Build safe filename
    advice_no = note_data.get("advice_note_no", note_id)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in advice_no)
    
    # Filename suffix depending on export_type and validity_type
    suffix_parts = []
    if export_type == "execution_log":
        suffix_parts.append("actions_log")
    if validity_type in ("valid", "expired"):
        suffix_parts.append(validity_type)
        
    suffix = f"_{'_'.join(suffix_parts)}" if suffix_parts else ""
    filename = f"InvestmentAdviceNote_{safe_name}{suffix}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )



