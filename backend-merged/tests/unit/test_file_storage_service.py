"""
Unit tests for File Storage Service.
"""
import pytest
import tempfile
import shutil
from pathlib import Path

from app.modules.kyc.application.services.file_storage_service import FileStorageService


class TestFileStorageService:
    """Test FileStorageService."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def storage_service(self, temp_dir):
        """Create file storage service with temp directory."""
        return FileStorageService(base_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_save_file(self, storage_service):
        """Test saving file."""
        file_bytes = b"fake file content"
        user_id = "user-123"
        file_type = "id_front"
        
        file_path = await storage_service.save_file(
            file_bytes=file_bytes,
            user_id=user_id,
            file_type=file_type,
            extension="jpg",
        )
        
        assert file_path is not None
        assert user_id in file_path
        assert file_type in file_path
        assert file_path.endswith(".jpg")
    
    @pytest.mark.asyncio
    async def test_read_file(self, storage_service):
        """Test reading file."""
        file_bytes = b"test content"
        user_id = "user-123"
        
        file_path = await storage_service.save_file(
            file_bytes=file_bytes,
            user_id=user_id,
            file_type="test",
            extension="txt",
        )
        
        read_bytes = await storage_service.read_file(file_path)
        
        assert read_bytes == file_bytes
    
    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, storage_service):
        """Test reading non-existent file."""
        result = await storage_service.read_file("nonexistent/path.jpg")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_file(self, storage_service):
        """Test deleting file."""
        file_bytes = b"test content"
        user_id = "user-123"
        
        file_path = await storage_service.save_file(
            file_bytes=file_bytes,
            user_id=user_id,
            file_type="test",
            extension="txt",
        )
        
        deleted = await storage_service.delete_file(file_path)
        
        assert deleted is True
        
        read_result = await storage_service.read_file(file_path)
        assert read_result is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, storage_service):
        """Test deleting non-existent file."""
        deleted = await storage_service.delete_file("nonexistent/path.jpg")
        
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_save_multiple_files_same_user(self, storage_service):
        """Test saving multiple files for same user."""
        user_id = "user-123"
        
        path1 = await storage_service.save_file(
            file_bytes=b"file1",
            user_id=user_id,
            file_type="id_front",
            extension="jpg",
        )
        
        path2 = await storage_service.save_file(
            file_bytes=b"file2",
            user_id=user_id,
            file_type="id_back",
            extension="jpg",
        )
        
        assert path1 != path2
        assert user_id in path1
        assert user_id in path2
