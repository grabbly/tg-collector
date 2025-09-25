"""
Unit tests for deterministic filename builder.

Tests the naming.py module which creates consistent, safe filenames
based on timestamp, chat_id, message_id, and message type.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.lib.naming import build_stem, build_paths


class TestFilenameBuilder:
    """Tests for filename building functions."""
    
    def test_build_stem_basic(self) -> None:
        """Test basic stem building with standard inputs."""
        ts = datetime(2025, 9, 25, 14, 30, 45, tzinfo=timezone.utc)
        result = build_stem(ts, 123456789, 42, "text")
        
        # Should follow pattern: {ts_utc}-{chat_id}-{message_id}-{type}
        expected = "20250925143045-123456789-42-text"
        assert result == expected
    
    def test_build_stem_audio_type(self) -> None:
        """Test stem building for audio messages."""
        ts = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = build_stem(ts, 999, 1, "audio")
        
        expected = "20250101000000-999-1-audio"
        assert result == expected
    
    def test_build_stem_stability(self) -> None:
        """Test that same inputs always produce same stem."""
        ts = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        chat_id, message_id, msg_type = 987654321, 100, "text"
        
        result1 = build_stem(ts, chat_id, message_id, msg_type)
        result2 = build_stem(ts, chat_id, message_id, msg_type)
        
        assert result1 == result2
        assert result1 == "20251231235959-987654321-100-text"
    
    def test_build_paths_with_extension(self) -> None:
        """Test building full paths with extension."""
        base_dir = Path("/storage")
        date_parts = (2025, 9, 25)  # year, month, day
        stem = "20250925143045-123456789-42-text"
        
        text_path, json_path = build_paths(base_dir, date_parts, stem, "txt")
        
        expected_text = Path("/storage/2025/09/25/20250925143045-123456789-42-text.txt")
        expected_json = Path("/storage/2025/09/25/20250925143045-123456789-42-text.json")
        
        assert text_path == expected_text
        assert json_path == expected_json
    
    def test_build_paths_audio_extension(self) -> None:
        """Test path building for audio files."""
        base_dir = Path("/data")
        date_parts = (2025, 2, 14)
        stem = "20250214120000-555-99-audio"
        
        audio_path, json_path = build_paths(base_dir, date_parts, stem, "ogg")
        
        expected_audio = Path("/data/2025/02/14/20250214120000-555-99-audio.ogg")
        expected_json = Path("/data/2025/02/14/20250214120000-555-99-audio.json")
        
        assert audio_path == expected_audio
        assert json_path == expected_json
    
    def test_build_paths_creates_date_hierarchy(self) -> None:
        """Test that paths include proper date-based folder structure."""
        base_dir = Path("/archive")
        date_parts = (2025, 12, 3)  # Single-digit month/day
        stem = "test-stem"
        
        file_path, json_path = build_paths(base_dir, date_parts, stem, "txt")
        
        # Should pad single digits with zero
        assert file_path.parent == Path("/archive/2025/12/03")
        assert json_path.parent == Path("/archive/2025/12/03")
    
    def test_edge_cases_large_ids(self) -> None:
        """Test with large chat/message IDs."""
        ts = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        large_chat_id = 9223372036854775807  # Max int64
        large_msg_id = 2147483647  # Max int32
        
        result = build_stem(ts, large_chat_id, large_msg_id, "audio")
        
        # Should handle large numbers without issue
        expected = f"20250615120000-{large_chat_id}-{large_msg_id}-audio"
        assert result == expected
        assert len(result) > 50  # Sanity check for long filename