"""
Investor IPS Document Routes — Bridge Proxy
────────────────────────────────────────────
Proxies Investment Policy Statement upload/list/download to the tenant's Bridge.
"""
from fastapi import APIRouter, Depends, UploadFile, File

from app.api.deps import get_bridge_client, get_current_user
from app.services.bridge_client import BridgeClient

router = APIRouter()


@router.post("/investor-members/{client_id}/{member_id}/ips-upload")
async def upload_investor_ips(
    client_id: str,
    member_id: str,
    file: UploadFile = File(...),
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    content = await file.read()
    return await bridge.upload_file(
        f"/investor-members/{client_id}/{member_id}/ips-upload",
        file_bytes=content,
        filename=file.filename,
        content_type="application/pdf",
    )


@router.get("/investor-members/{client_id}/{member_id}/ips-documents")
async def list_investor_ips(
    client_id: str,
    member_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    return await bridge.get(f"/investor-members/{client_id}/{member_id}/ips-documents")


@router.get("/investor-members/{client_id}/{member_id}/ips-download/{doc_id}")
async def download_investor_ips(
    client_id: str,
    member_id: str,
    doc_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
    current_user=Depends(get_current_user),
):
    from fastapi.responses import StreamingResponse
    import httpx

    # Bridge returns a 302 to a presigned S3 URL or a local bridge static URL.
    # We must never redirect the browser to the bridge directly — the browser
    # cannot reach the bridge (different origin, no auth, CORS blocks OPTIONS).
    # Instead, fetch the file here in the backend and stream it to the client.
    bridge_response = await bridge.get_raw(
        f"/investor-members/{client_id}/{member_id}/ips-download/{doc_id}"
    )

    if bridge_response.status_code in (301, 302, 303, 307, 308):
        file_url = bridge_response.headers.get("location", "")
        async with httpx.AsyncClient(timeout=30) as client:
            file_resp = await client.get(file_url, follow_redirects=True)
        content = file_resp.content
    else:
        content = bridge_response.content

    cd = bridge_response.headers.get("content-disposition", "inline; filename=\"ips_document.pdf\"")
    return StreamingResponse(
        iter([content]),
        media_type="application/pdf",
        headers={"Content-Disposition": cd},
    )
