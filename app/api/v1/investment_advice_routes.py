"""
Investment Advice Note Routes — Bridge Proxy
─────────────────────────────────────────────
Proxies investment advice note requests to the tenant's Bridge.
Follows the same pattern as target_portfolio_routes.py.
"""
from fastapi import APIRouter, Depends, Query
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
    bridge: BridgeClient = Depends(get_bridge_client),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate and download the Investment Advice Note as a PDF."""
    from fastapi import HTTPException
    from app.utils.reports.investment_advice_report import InvestmentAdviceNotePDF

    # 1. Fetch the full note data (includes client_snapshot + recommendations)
    note_data = await bridge.get(f"/investment-advice-note/{note_id}")
    if not note_data or not isinstance(note_data, dict):
        raise HTTPException(404, "Advice note not found.")

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
    )

    # 4. Build safe filename
    advice_no = note_data.get("advice_note_no", note_id)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in advice_no)
    filename = f"InvestmentAdviceNote_{safe_name}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Download advice note as DOCX ─────────────────────────────────
@router.get("/investment-advice-note/{note_id}/export/docx")
async def download_advice_note_docx(
    note_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    """Generate and download the Investment Advice Note as a Word document."""
    from fastapi import HTTPException
    from app.utils.reports.investment_advice_report import InvestmentAdviceNoteDOCX

    # 1. Fetch the full note data
    note_data = await bridge.get(f"/investment-advice-note/{note_id}")
    if not note_data or not isinstance(note_data, dict):
        raise HTTPException(404, "Advice note not found.")

    # 2. Fetch IA master data
    ia_data = await bridge.get("/ia-master")
    ia_dict = ia_data if isinstance(ia_data, dict) else None

    # 3. Generate DOCX
    docx_buffer = InvestmentAdviceNoteDOCX.generate_docx(
        note_data=note_data,
        ia_data=ia_dict,
    )

    # 4. Build safe filename
    advice_no = note_data.get("advice_note_no", note_id)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in advice_no)
    filename = f"InvestmentAdviceNote_{safe_name}.docx"

    return Response(
        content=docx_buffer.read(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

