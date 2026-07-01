"""
Communication Routes — IA–Investor Thread-Based Messaging
──────────────────────────────────────────────────────────
Thin proxy layer. All business logic and data storage lives in the Bridge.
"""
import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from app.api.deps import get_bridge_client, get_current_user
from app.services.bridge_client import BridgeClient

logger = logging.getLogger("significia.communication_routes")

router = APIRouter()


@router.get("/stats")
async def get_communication_stats(
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user: Any = Depends(get_current_user),
):
    """Inbox summary — unread counts and thread status breakdown."""
    return await bridge.get("/communication/stats")


@router.get("/threads")
async def list_threads(
    client_id: str = Query(None),
    status: str = Query(None),
    thread_type: str = Query(None),
    search: str = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user: Any = Depends(get_current_user),
):
    """List threads with optional filters. Paginated."""
    params = {"limit": limit, "offset": offset}
    if client_id:
        params["client_id"] = client_id
    if status:
        params["status"] = status
    if thread_type:
        params["thread_type"] = thread_type
    if search:
        params["search"] = search
    return await bridge.get("/communication/threads", params=params)


@router.post("/threads")
async def create_thread(
    payload: dict,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user: Any = Depends(get_current_user),
):
    """Start a new conversation thread with a client."""
    return await bridge.post("/communication/threads", payload)


@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user: Any = Depends(get_current_user),
):
    """Retrieve a full thread with all messages."""
    return await bridge.get(f"/communication/threads/{thread_id}")


@router.post("/threads/{thread_id}/attachments")
async def upload_attachments(
    thread_id: str,
    files: List[UploadFile] = File(...),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user: Any = Depends(get_current_user),
):
    """Upload files for a thread message. Returns storage keys."""
    files_list = []
    for f in files:
        content = await f.read()
        files_list.append(("files", (f.filename, content, f.content_type or "application/octet-stream")))
    return await bridge.post(
        f"/communication/threads/{thread_id}/attachments",
        files=files_list,
    )


@router.post("/threads/{thread_id}/messages")
async def add_message(
    thread_id: str,
    body: str = Form(...),
    sender_type: str = Form("IA"),
    source: str = Form("COMPOSED"),
    is_internal_note: str = Form("false"),
    files: Optional[List[UploadFile]] = File(None),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user: Any = Depends(get_current_user),
):
    """Add a message to a thread (IA compose or log a client reply)."""
    form_data = {
        "body": body,
        "sender_type": sender_type,
        "source": source,
        "is_internal_note": is_internal_note,
    }
    files_list = []
    if files:
        for f in files:
            content = await f.read()
            files_list.append(("files", (f.filename, content, f.content_type or "application/octet-stream")))

    return await bridge.post(
        f"/communication/threads/{thread_id}/messages",
        data=form_data,
        files=files_list if files_list else None,
    )


@router.patch("/threads/{thread_id}/status")
async def update_thread_status(
    thread_id: str,
    payload: dict,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user: Any = Depends(get_current_user),
):
    """Update thread status: OPEN | CLOSED | PENDING_IA | PENDING_CLIENT."""
    return await bridge.patch(f"/communication/threads/{thread_id}/status", payload)


@router.patch("/threads/{thread_id}/read")
async def mark_thread_read(
    thread_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user: Any = Depends(get_current_user),
):
    """Mark all unread client messages in a thread as read."""
    return await bridge.patch(f"/communication/threads/{thread_id}/read", {})


@router.get("/threads/{thread_id}/export")
async def export_thread(
    thread_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user: Any = Depends(get_current_user),
):
    """Export full thread with per-message audit hash verification for SEBI submission."""
    return await bridge.get(f"/communication/threads/{thread_id}/export")
