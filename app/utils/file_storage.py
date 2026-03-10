import os
import uuid
from datetime import datetime
import shutil
import anyio
from pathlib import Path
from fastapi import UploadFile
from werkzeug.utils import secure_filename

UPLOAD_DIR = "uploads/ia_documents"

async def save_upload_file(upload_file: UploadFile, nature_of_entity: str, prefix: str) -> str:
    """
    Saves a FastAPI UploadFile to the local filesystem.
    Returns the relative path to the saved file.
    """
    # Create directory structure
    target_dir = os.path.join(UPLOAD_DIR, nature_of_entity)
    os.makedirs(target_dir, exist_ok=True)
    
    # Generate secure filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(upload_file.filename)[1]
    # We want to keep the original extension and sanitize the rest
    base_name = f"{prefix}_{timestamp}_{uuid.uuid4().hex[:8]}"
    filename = secure_filename(f"{base_name}{ext}")
    
    # Physical path
    file_path = os.path.join(target_dir, filename)
    
    # Write the file asynchronously
    async with await anyio.open_file(file_path, "wb") as f:
        while content := await upload_file.read(1024 * 1024): # 1MB chunks
            await f.write(content)
            
    # Reset file pointer just in case it's needed elsewhere
    await upload_file.seek(0)
        
    return file_path
