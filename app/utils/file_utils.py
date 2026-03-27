import os
import uuid
import tempfile
import httpx
from typing import Optional
from sqlalchemy.orm import Session
from app.services.storage_service import StorageService

async def resolve_logo_to_local_path(db_path: Optional[str], db: Session) -> Optional[str]:
    """
    Resolves a database path (local, cloud key, or URL) to a local filesystem path.
    Downloads cloud/remote files to temporary storage if necessary.
    """
    with open("debug_logo.log", "a") as f:
        f.write(f"\nDEBUG: resolve_logo_to_local_path called with db_path: {db_path}\n")
    if not db_path:
        with open("debug_logo.log", "a") as f:
            f.write("DEBUG: db_path is empty/None\n")
        return None

    # 1. Full URL (e.g. from a cloud provider or external link)
    if db_path.startswith(("http://", "https://")):
        try:
            with open("debug_logo.log", "a") as f:
                f.write(f"DEBUG: Attempting to download from URL: {db_path}\n")
            async with httpx.AsyncClient() as client:
                resp = await client.get(db_path)
                if resp.status_code == 200:
                    ext = os.path.splitext(db_path.split('?')[0])[1] or '.png'
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                    tmp.write(resp.content)
                    tmp.close()
                    with open("debug_logo.log", "a") as f:
                        f.write(f"DEBUG: Downloaded to temp file: {tmp.name}\n")
                    return tmp.name
                else:
                    with open("debug_logo.log", "a") as f:
                        f.write(f"DEBUG: Download failed with status {resp.status_code}\n")
        except Exception as e:
            with open("debug_logo.log", "a") as f:
                f.write(f"DEBUG: Failed to download logo from URL {db_path}: {e}\n")
            return None

    # 2. Cloud Storage Key (e.g. docs/nature/filename)
    elif db_path.startswith("docs/"):
        with open("debug_logo.log", "a") as f:
            f.write(f"DEBUG: Cloud Key detected: {db_path}\n")
        driver = StorageService.get_tenant_storage(db)
        if driver:
            try:
                with open("debug_logo.log", "a") as f:
                    f.write("DEBUG: Fetching from cloud storage...\n")
                file_bytes = await driver.download_file(db_path)
                if file_bytes:
                    ext = os.path.splitext(db_path)[1] or '.png'
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                    tmp.write(file_bytes)
                    tmp.close()
                    with open("debug_logo.log", "a") as f:
                        f.write(f"DEBUG: Cloud file saved to temp: {tmp.name}\n")
                    return tmp.name
                else:
                    with open("debug_logo.log", "a") as f:
                        f.write("DEBUG: download_file returned empty bytes\n")
            except Exception as e:
                with open("debug_logo.log", "a") as f:
                    f.write(f"DEBUG: Failed to download logo from cloud storage {db_path}: {e}\n")
                return None
        else:
            with open("debug_logo.log", "a") as f:
                f.write("DEBUG: Storage driver not found for cloud key\n")

    # 3. Local Storage Path
    else:
        with open("debug_logo.log", "a") as f:
            f.write(f"DEBUG: Local path detected: {db_path}\n")
        # Try relative to CWD first (server root)
        abs_path = os.path.abspath(db_path)
        with open("debug_logo.log", "a") as f:
            f.write(f"DEBUG: Checking abspath: {abs_path}\n")
        if os.path.exists(abs_path):
            with open("debug_logo.log", "a") as f:
                f.write("DEBUG: Found at abspath\n")
            return abs_path
        
        # Try relative to backend root specifically if called from a submodule
        file_dir = os.path.dirname(os.path.abspath(__file__))
        backend_root = os.path.abspath(os.path.join(file_dir, '..', '..'))
        joined_path = os.path.join(backend_root, db_path)
        with open("debug_logo.log", "a") as f:
            f.write(f"DEBUG: Checking joined path: {joined_path}\n")
        if os.path.exists(joined_path):
            with open("debug_logo.log", "a") as f:
                f.write("DEBUG: Found at joined path\n")
            return joined_path

    with open("debug_logo.log", "a") as f:
        f.write("DEBUG: NO PATH RESOLVED\n")
    return None
