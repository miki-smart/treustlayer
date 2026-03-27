"""
File Storage Service — local file storage for KYC documents.
"""
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

import aiofiles

from app.core.config import settings

logger = logging.getLogger(__name__)


class FileStorageService:
    """
    Local file storage for KYC documents.
    
    In production, this should be replaced with S3/GCS/Azure Blob Storage.
    """
    
    def __init__(self, base_path: str = "uploads/kyc"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def save_file(
        self, file_bytes: bytes, user_id: str, file_type: str, extension: str = "jpg"
    ) -> str:
        """
        Save file to disk.
        
        Args:
            file_bytes: File content
            user_id: User ID (for organizing files)
            file_type: Type of file (id_front, id_back, utility_bill, face_image)
            extension: File extension
        
        Returns:
            Relative file path
        """
        user_dir = self.base_path / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{file_type}_{uuid.uuid4().hex[:8]}.{extension}"
        file_path = user_dir / filename
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes)
        
        relative_path = str(file_path.relative_to(self.base_path.parent))
        
        logger.info(f"File saved: {relative_path}")
        
        return relative_path
    
    async def read_file(self, file_path: str) -> Optional[bytes]:
        """
        Read file from disk.
        
        Args:
            file_path: Relative file path
        
        Returns:
            File bytes or None if not found
        """
        full_path = self.base_path.parent / file_path
        
        if not full_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None
        
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from disk.
        
        Args:
            file_path: Relative file path
        
        Returns:
            True if deleted, False if not found
        """
        full_path = self.base_path.parent / file_path
        
        if not full_path.exists():
            return False
        
        full_path.unlink()
        logger.info(f"File deleted: {file_path}")
        
        return True
