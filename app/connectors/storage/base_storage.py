from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from fastapi import UploadFile

class BaseStorage(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def upload_file(self, file: UploadFile, remote_path: str) -> str:
        """Upload a file to the storage provider."""
        pass

    @abstractmethod
    async def get_file_url(self, remote_path: str, expires_in: int = 3600) -> str:
        """Generate a secure URL for file access."""
        pass

    @abstractmethod
    async def delete_file(self, remote_path: str) -> bool:
        """Delete a file from the storage provider."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the storage connection is valid."""
        pass

    @abstractmethod
    async def download_file(self, remote_path: str) -> Optional[bytes]:
        """Download a file from the storage provider and return bytes."""
        pass
