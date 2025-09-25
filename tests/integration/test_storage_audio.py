"""Integration tests for audio storage service."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.services.storage import save_audio


class TestSaveAudioIntegration:
    """Test saving audio files with metadata."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_audio_data(self):
        """Sample audio data (mock OGG content)."""
        return b"\x4f\x67\x67\x53\x00\x02\x00\x00" + b"fake ogg audio data" * 10

    def test_save_audio_creates_ogg_and_json_files(self, temp_storage_dir, sample_audio_data):
        """Test that save_audio creates both .ogg and .json files with same stem."""
        chat_id = 12345
        message_id = 67890
        mime_type = "audio/ogg"
        extension = "ogg"
        ts_utc = datetime(2025, 1, 15, 14, 30, 0)
        
        # Save audio
        ogg_path, json_path = save_audio(temp_storage_dir, chat_id, message_id, sample_audio_data, mime_type, extension, ts_utc)
        
        # Check both files exist with same stem
        assert ogg_path.exists()
        assert json_path.exists()
        assert ogg_path.stem == json_path.stem
        
        # Verify filename format (YYYYMMDDHHMMSS format)
        expected_stem = "20250115143000-12345-67890-audio"
        assert ogg_path.stem == expected_stem
        assert json_path.stem == expected_stem

    def test_save_audio_stores_correct_audio_content(self, temp_storage_dir, sample_audio_data):
        """Test that audio content is stored correctly."""
        chat_id = 11111
        message_id = 22222
        mime_type = "audio/ogg"
        extension = "ogg"
        ts_utc = datetime(2025, 2, 20, 10, 15, 30)
        
        # Save audio
        ogg_path, json_path = save_audio(temp_storage_dir, chat_id, message_id, sample_audio_data, mime_type, extension, ts_utc)
        
        # Read back the audio file
        with open(ogg_path, 'rb') as f:
            stored_content = f.read()
        
        assert stored_content == sample_audio_data

    def test_save_audio_creates_metadata_json(self, temp_storage_dir, sample_audio_data):
        """Test that metadata JSON is created with correct fields."""
        chat_id = 33333
        message_id = 44444
        mime_type = "audio/ogg"
        extension = "ogg"
        ts_utc = datetime(2025, 3, 10, 16, 45, 0)
        
        # Save audio
        ogg_path, json_path = save_audio(temp_storage_dir, chat_id, message_id, sample_audio_data, mime_type, extension, ts_utc)
        
        # Read metadata JSON
        with open(json_path, 'r') as f:
            metadata = json.load(f)
        
        # Check required fields (matching actual storage implementation)
        assert metadata["type"] == "audio"
        assert metadata["chat_id"] == 33333
        assert metadata["message_id"] == 44444
        assert metadata["mime_type"] == "audio/ogg"
        assert metadata["timestamp"] == "2025-03-10T16:45:00"  # ISO format without timezone
        assert metadata["file_size"] == len(sample_audio_data)
        assert "checksum" in metadata
        assert len(metadata["checksum"]) == 64  # SHA256 hex length

    def test_save_audio_computes_correct_checksum(self, temp_storage_dir, sample_audio_data):
        """Test that SHA256 checksum is computed correctly."""
        import hashlib
        
        chat_id = 55555
        message_id = 66666
        mime_type = "audio/ogg"
        extension = "ogg"
        ts_utc = datetime(2025, 4, 5, 12, 0, 0)
        
        # Compute expected checksum
        expected_checksum = hashlib.sha256(sample_audio_data).hexdigest()
        
        # Save audio
        ogg_path, json_path = save_audio(temp_storage_dir, chat_id, message_id, sample_audio_data, mime_type, extension, ts_utc)
        
        # Check checksum in metadata
        with open(json_path, 'r') as f:
            metadata = json.load(f)
        
        assert metadata["checksum"] == expected_checksum

    def test_save_audio_respects_file_permissions(self, temp_storage_dir, sample_audio_data):
        """Test that saved files respect umask permissions."""
        chat_id = 99999
        message_id = 11111
        mime_type = "audio/ogg"
        extension = "ogg"
        ts_utc = datetime(2025, 6, 15, 20, 10, 0)
        
        # Save audio
        ogg_path, json_path = save_audio(temp_storage_dir, chat_id, message_id, sample_audio_data, mime_type, extension, ts_utc)
        
        # Check file permissions
        ogg_stat = os.stat(ogg_path)
        json_stat = os.stat(json_path)
        
        # Check owner read/write permissions
        assert ogg_stat.st_mode & 0o600 == 0o600
        assert json_stat.st_mode & 0o600 == 0o600

    def test_save_audio_different_extensions(self, temp_storage_dir, sample_audio_data):
        """Test saving audio with different valid extensions."""
        test_cases = [
            ("audio/ogg", "ogg"),
            ("audio/mpeg", "mp3"),
            ("audio/wav", "wav"),
            ("audio/x-m4a", "m4a"),
        ]
        
        for i, (mime_type, extension) in enumerate(test_cases):
            chat_id = 10000 + i
            message_id = 20000 + i
            ts_utc = datetime(2025, 8, 10 + i, 14, 0, 0)
            
            # Save audio
            ogg_path, json_path = save_audio(temp_storage_dir, chat_id, message_id, sample_audio_data, mime_type, extension, ts_utc)
            
            # Verify correct extension
            assert ogg_path.suffix == f".{extension}"
            assert json_path.suffix == ".json"

    def test_save_audio_unicode_handling(self, temp_storage_dir):
        """Test that audio saving handles Unicode metadata correctly."""
        # Audio data with some non-ASCII bytes
        audio_data = "привет мир".encode('utf-8') + b"\x00\x01\x02"
        
        chat_id = 13579
        message_id = 24680
        mime_type = "audio/ogg"
        extension = "ogg"
        ts_utc = datetime(2025, 9, 25, 13, 45, 0)
        
        # Save audio
        ogg_path, json_path = save_audio(temp_storage_dir, chat_id, message_id, audio_data, mime_type, extension, ts_utc)
        
        # Check audio content
        with open(ogg_path, 'rb') as f:
            stored_content = f.read()
        assert stored_content == audio_data
        
        # Check JSON can be parsed (valid UTF-8)
        with open(json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        assert metadata["file_size"] == len(audio_data)