"""
Storage Routes — File URL & Download Proxy
───────────────────────────────────────────
Thin proxy to the Bridge storage service.
"""
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.deps import get_bridge_client, get_current_user
from app.services.bridge_client import BridgeClient

router = APIRouter()


@router.get("/url")
async def get_file_url(
    key: str = Query(...),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user: Any = Depends(get_current_user),
):
    """Get a pre-signed URL for a stored file."""
    return await bridge.get("/storage/url", params={"key": key})


@router.get("/file")
async def download_file(
    key: str = Query(...),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user: Any = Depends(get_current_user),
):
    """Proxy file bytes from storage — avoids browser CORS on direct storage URLs."""
    url_data = await bridge.get("/storage/url", params={"key": key})
    presigned_url = url_data.get("url")
    if not presigned_url:
        raise HTTPException(404, "File not found")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(presigned_url)
        if resp.status_code >= 400:
            raise HTTPException(resp.status_code, "Failed to fetch file from storage")

    content_type = resp.headers.get("content-type", "application/octet-stream")
    filename = key.split("/")[-1]

    return StreamingResponse(
        iter([resp.content]),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
