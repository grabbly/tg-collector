"""
Unit tests for MIME type and size validation.

Tests the validation.py module which validates audio MIME types,
file extensions, and enforces size limits per constitution.
"""

import pytest

from src.lib.validation import validate_mime_and_ext, validate_size, ValidationError


class TestMimeAndExtValidation:
    """Tests for MIME type and extension validation."""
    
    def test_accept_valid_ogg_opus(self) -> None:
        """Test that valid Telegram voice format is accepted."""
        # Telegram voice messages are audio/ogg with Opus codec
        result = validate_mime_and_ext("audio/ogg", "ogg")
        assert result is True
    
    def test_accept_common_audio_formats(self) -> None:
        """Test acceptance of common audio formats."""
        valid_combinations = [
            ("audio/ogg", "ogg"),
            ("audio/mpeg", "mp3"),
            ("audio/mp4", "m4a"),
            ("audio/wav", "wav"),
        ]
        
        for mime_type, ext in valid_combinations:
            assert validate_mime_and_ext(mime_type, ext) is True
    
    def test_reject_unsupported_mime_types(self) -> None:
        """Test rejection of unsupported MIME types."""        
        invalid_types = [
            ("video/mp4", "mp4"),
            ("image/jpeg", "jpg"),
            ("application/pdf", "pdf"),
            ("text/plain", "txt"),
            ("audio/unknown", "xyz"),
        ]
        
        for mime_type, ext in invalid_types:
            with pytest.raises(ValidationError):
                validate_mime_and_ext(mime_type, ext)
    
    def test_reject_mismatched_mime_and_ext(self) -> None:
        """Test rejection when MIME type doesn't match extension."""
        mismatches = [
            ("audio/ogg", "mp3"),  # OGG MIME with MP3 extension
            ("audio/mpeg", "ogg"),  # MP3 MIME with OGG extension
            ("audio/wav", "mp4"),   # WAV MIME with MP4 extension
        ]
        
        for mime_type, ext in mismatches:
            with pytest.raises(ValidationError):
                validate_mime_and_ext(mime_type, ext)
    
    def test_case_insensitive_extensions(self) -> None:
        """Test that extensions are handled case-insensitively."""
        # Should accept both lowercase and uppercase extensions
        assert validate_mime_and_ext("audio/ogg", "OGG") is True
        assert validate_mime_and_ext("audio/mpeg", "MP3") is True
        assert validate_mime_and_ext("audio/wav", "Wav") is True


class TestSizeValidation:
    """Tests for file size validation."""
    
    def test_accept_small_files(self) -> None:
        """Test that small files are accepted."""
        small_sizes = [100, 1024, 1024 * 10, 1024 * 100]  # Up to 100KB
        limit = 1024 * 1024  # 1MB limit
        
        for size in small_sizes:
            assert validate_size(size, limit) is True
    
    def test_accept_files_at_limit(self) -> None:
        """Test that files exactly at the limit are accepted."""
        limit = 1024 * 1024 * 50  # 50MB
        assert validate_size(limit, limit) is True
    
    def test_reject_oversized_files(self) -> None:
        """Test that files over the limit are rejected."""
        limit = 1024 * 1024 * 10  # 10MB
        oversized = [
            limit + 1,
            limit * 2,
            limit * 10,
            1024 * 1024 * 1024,  # 1GB
        ]
        
        for size in oversized:
            with pytest.raises(ValidationError):
                validate_size(size, limit)
    
    def test_reject_negative_sizes(self) -> None:
        """Test that negative sizes are rejected."""
        with pytest.raises(ValidationError):
            validate_size(-1, 1024)
        
        with pytest.raises(ValidationError):
            validate_size(-1000, 1024 * 1024)
    
    def test_reject_zero_size(self) -> None:
        """Test that zero-byte files are rejected."""
        with pytest.raises(ValidationError):
            validate_size(0, 1024 * 1024)
    
    def test_default_audio_limit(self) -> None:
        """Test validation with typical audio file limit (50MB)."""
        limit = 52428800  # 50MB (from config default)
        
        # Should accept typical voice message sizes
        typical_sizes = [
            1024 * 100,      # 100KB
            1024 * 1024,     # 1MB
            1024 * 1024 * 5, # 5MB
            limit - 1000,    # Just under limit
        ]
        
        for size in typical_sizes:
            assert validate_size(size, limit) is True
        
        # Should reject files over 50MB
        with pytest.raises(ValidationError):
            validate_size(limit + 1, limit)