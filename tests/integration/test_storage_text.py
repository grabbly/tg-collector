"""
Integration tests for text storage with atomic writes and metadata.

Tests the storage.py module's text saving functionality including:
- Atomic write (tmp -> fsync -> rename)
- Metadata JSON generation with required fields
- File permissions respect umask
- Checksum generation for text content
"""

import json
import os
import pytest
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from src.services.storage import save_text, StorageError


class TestTextStorage:
    """Integration tests for text message storage."""
    
    def setup_method(self) -> None:
        """Set up test environment with temp directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.storage_base = self.temp_dir / "storage"
        self.storage_base.mkdir()
    
    def teardown_method(self) -> None:
        """Clean up test files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_save_text_creates_file_and_metadata(self) -> None:
        """Test that text is saved with paired metadata JSON."""
        chat_id = 123456789
        message_id = 42
        text_content = "Hello, this is a test message!"
        timestamp = datetime(2025, 9, 25, 14, 30, 45, tzinfo=timezone.utc)
        
        # Save text and get paths
        text_path, json_path = save_text(
            base_dir=self.storage_base,
            chat_id=chat_id,
            message_id=message_id,
            text=text_content,
            timestamp=timestamp
        )
        
        # Verify text file exists and has correct content
        assert text_path.exists()
        assert text_path.read_text(encoding="utf-8") == text_content
        
        # Verify metadata JSON exists and has required fields
        assert json_path.exists()
        metadata = json.loads(json_path.read_text(encoding="utf-8"))
        
        expected_fields = {
            "timestamp", "chat_id", "message_id", "sender_id",
            "type", "file_size", "mime_type", "checksum", "storage_path"
        }
        assert set(metadata.keys()) == expected_fields
        
        # Verify specific values
        assert metadata["timestamp"] == "2025-09-25T14:30:45+00:00"
        assert metadata["chat_id"] == chat_id
        assert metadata["message_id"] == message_id
        assert metadata["type"] == "text"
        assert metadata["file_size"] == len(text_content.encode("utf-8"))
        assert metadata["mime_type"] == "text/plain"
        assert len(metadata["checksum"]) == 64  # SHA256 hex length
        assert metadata["storage_path"] == str(text_path)
    
    def test_save_text_uses_date_hierarchy(self) -> None:
        """Test that files are organized in date-based folders."""
        timestamp = datetime(2025, 12, 3, 9, 15, 30, tzinfo=timezone.utc)
        
        text_path, json_path = save_text(
            base_dir=self.storage_base,
            chat_id=999,
            message_id=1,
            text="Test content",
            timestamp=timestamp
        )
        
        # Should be in YYYY/MM/DD folder structure
        expected_parent = self.storage_base / "2025" / "12" / "03"
        assert text_path.parent == expected_parent
        assert json_path.parent == expected_parent
        
        # Verify the date folders were created
        assert expected_parent.exists()
        assert expected_parent.is_dir()
    
    def test_save_text_deterministic_filenames(self) -> None:
        """Test that filenames follow the deterministic pattern."""
        timestamp = datetime(2025, 1, 15, 10, 20, 30, tzinfo=timezone.utc)
        chat_id = 555666777
        message_id = 789
        
        text_path, json_path = save_text(
            base_dir=self.storage_base,
            chat_id=chat_id,
            message_id=message_id,
            text="Content",
            timestamp=timestamp
        )
        
        # Should follow pattern: {ts}-{chat_id}-{message_id}-text.{ext}
        expected_stem = "20250115102030-555666777-789-text"
        assert text_path.name == f"{expected_stem}.txt"
        assert json_path.name == f"{expected_stem}.json"
    
    def test_save_text_atomic_write(self) -> None:
        """Test that files are written atomically (no partial writes visible)."""
        large_text = "A" * 10000  # Large enough to test atomicity
        
        text_path, json_path = save_text(
            base_dir=self.storage_base,
            chat_id=111,
            message_id=222,
            text=large_text,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Files should appear complete, not partial
        assert text_path.read_text() == large_text
        
        # Metadata should be written last (after text file exists)
        metadata = json.loads(json_path.read_text())
        assert Path(metadata["storage_path"]).exists()
    
    def test_save_text_checksum_consistency(self) -> None:
        """Test that checksum in metadata matches file content."""
        import hashlib
        
        text_content = "Test message for checksum verification"
        expected_checksum = hashlib.sha256(text_content.encode("utf-8")).hexdigest()
        
        _, json_path = save_text(
            base_dir=self.storage_base,
            chat_id=123,
            message_id=456,
            text=text_content,
            timestamp=datetime.now(timezone.utc)
        )
        
        metadata = json.loads(json_path.read_text())
        assert metadata["checksum"] == expected_checksum
    
    def test_save_text_unicode_content(self) -> None:
        """Test that Unicode text is handled correctly."""
        unicode_text = "🤖 Привет! 你好 こんにちは"
        
        text_path, json_path = save_text(
            base_dir=self.storage_base,
            chat_id=777,
            message_id=888,
            text=unicode_text,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Verify content round-trip
        saved_content = text_path.read_text(encoding="utf-8")
        assert saved_content == unicode_text
        
        # Verify size accounts for UTF-8 encoding
        metadata = json.loads(json_path.read_text())
        assert metadata["file_size"] == len(unicode_text.encode("utf-8"))
    
    def test_save_text_missing_base_directory_error(self) -> None:
        """Test error handling when base directory doesn't exist."""
        nonexistent_dir = self.temp_dir / "missing"
        
        with pytest.raises(StorageError):
            save_text(
                base_dir=nonexistent_dir,
                chat_id=123,
                message_id=456,
                text="test",
                timestamp=datetime.now(timezone.utc)
            )
    
    def test_save_text_minimal_pii_metadata(self) -> None:
        """Test that metadata contains minimal PII per constitution."""
        _, json_path = save_text(
            base_dir=self.storage_base,
            chat_id=999999,
            message_id=1001,
            text="Privacy test",
            timestamp=datetime.now(timezone.utc)
        )
        
        metadata = json.loads(json_path.read_text())
        
        # Should have sender_id as numeric only (no username/full name)
        assert "sender_id" in metadata
        assert isinstance(metadata["sender_id"], (int, type(None)))
        
        # Should NOT contain sensitive fields
        forbidden_fields = {"username", "full_name", "phone", "email", "raw_message"}
        assert not any(field in metadata for field in forbidden_fields)