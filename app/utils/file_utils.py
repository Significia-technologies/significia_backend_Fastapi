import os
import uuid
import tempfile
import httpx
from typing import Optional
from sqlalchemy.orm import Session

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

    # 2. Local Storage Path
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
