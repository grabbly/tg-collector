"""
Atomic filesystem storage service for ArchiveDrop.

Handles saving text and audio messages with paired metadata JSON files.
Implements constitutional requirements:
- Atomic writes (tmp -> fsync -> rename)  
- Minimal PII in metadata
- Deterministic filenames and date hierarchy
- SHA256 checksums for integrity
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from src.lib.naming import build_stem, build_paths


class StorageError(Exception):
    """Raised when storage operations fail."""
    pass


def save_text(
    base_dir: Path,
    chat_id: int,
    message_id: int,
    text: str,
    timestamp: datetime,
    sender_id: Optional[int] = None
) -> Tuple[Path, Path]:
    """
    Save text message atomically with metadata JSON.
    
    Args:
        base_dir: Base storage directory
        chat_id: Telegram chat ID
        message_id: Telegram message ID  
        text: Message text content
        timestamp: UTC timestamp
        sender_id: Optional numeric sender ID (minimal PII)
    
    Returns:
        Tuple of (text_file_path, metadata_json_path)
        
    Raises:
        StorageError: If storage operations fail
    """
    if not base_dir.exists():
        raise StorageError(f"Base storage directory does not exist: {base_dir}")
    
    try:
        # Build filename stem and paths
        stem = build_stem(timestamp, chat_id, message_id, "text")
        date_parts = (timestamp.year, timestamp.month, timestamp.day)
        text_path, json_path = build_paths(base_dir, date_parts, stem, "txt")
        
        # Create date directory if needed
        text_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Encode text and compute checksum
        text_bytes = text.encode("utf-8")
        checksum = hashlib.sha256(text_bytes).hexdigest()
        
        # Atomic write: tmp -> fsync -> rename
        text_tmp = text_path.with_suffix(".tmp")
        try:
            with text_tmp.open("wb") as f:
                f.write(text_bytes)
                f.flush()
                os.fsync(f.fileno())
            
            # Rename to final path (atomic on POSIX)
            text_tmp.rename(text_path)
            
        except Exception as e:
            # Clean up temp file on failure
            if text_tmp.exists():
                text_tmp.unlink()
            raise StorageError(f"Failed to write text file: {e}")
        
        # Create metadata JSON (after text file exists)
        metadata = {
            "timestamp": timestamp.isoformat(),
            "chat_id": chat_id,
            "message_id": message_id,
            "type": "text",
            "size": len(text_bytes),
            "mime_type": "text/plain",
            "checksum": checksum,
            "storage_path": str(text_path)
        }
        
        # Atomic write for metadata JSON
        json_tmp = json_path.with_suffix(".tmp")
        try:
            with json_tmp.open("w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            
            json_tmp.rename(json_path)
            
        except Exception as e:
            # Clean up on failure
            if json_tmp.exists():
                json_tmp.unlink()
            # Also remove text file since metadata failed
            if text_path.exists():
                text_path.unlink()
            raise StorageError(f"Failed to write metadata JSON: {e}")
        
        return text_path, json_path
        
    except Exception as e:
        if isinstance(e, StorageError):
            raise
        raise StorageError(f"Unexpected error during text save: {e}")


def save_audio(
    base_dir: Path,
    chat_id: int,
    message_id: int,
    audio_data: bytes,
    mime_type: str,
    extension: str,
    timestamp: datetime,
    sender_id: Optional[int] = None,
    duration: Optional[int] = None
) -> Tuple[Path, Path]:
    """
    Save audio message atomically with metadata JSON.
    
    Args:
        base_dir: Base storage directory
        chat_id: Telegram chat ID
        message_id: Telegram message ID
        audio_data: Audio file bytes
        mime_type: MIME type (e.g., "audio/ogg")
        extension: File extension (e.g., "ogg")
        timestamp: UTC timestamp
        sender_id: Optional numeric sender ID (minimal PII)
    
    Returns:
        Tuple of (audio_file_path, metadata_json_path)
        
    Raises:
        StorageError: If storage operations fail
    """
    if not base_dir.exists():
        raise StorageError(f"Base storage directory does not exist: {base_dir}")
    
    try:
        # Build filename stem and paths
        stem = build_stem(timestamp, chat_id, message_id, "audio")
        date_parts = (timestamp.year, timestamp.month, timestamp.day)
        audio_path, json_path = build_paths(base_dir, date_parts, stem, extension)
        
        # Create date directory if needed
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Compute checksum
        checksum = hashlib.sha256(audio_data).hexdigest()
        
        # Atomic write: tmp -> fsync -> rename
        audio_tmp = audio_path.with_suffix(".tmp")
        try:
            with audio_tmp.open("wb") as f:
                f.write(audio_data)
                f.flush()
                os.fsync(f.fileno())
            
            # Rename to final path (atomic on POSIX)
            audio_tmp.rename(audio_path)
            
        except Exception as e:
            # Clean up temp file on failure
            if audio_tmp.exists():
                audio_tmp.unlink()
            raise StorageError(f"Failed to write audio file: {e}")
        
        # Create metadata JSON (after audio file exists)
        metadata = {
            "timestamp": timestamp.isoformat(),
            "chat_id": chat_id,
            "message_id": message_id,
            "type": "audio",
            "size": len(audio_data),
            "mime_type": mime_type,
            "duration": duration,
            "checksum": checksum,
            "storage_path": str(audio_path)
        }
        
        # Atomic write for metadata JSON
        json_tmp = json_path.with_suffix(".tmp")
        try:
            with json_tmp.open("w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            
            json_tmp.rename(json_path)
            
        except Exception as e:
            # Clean up on failure
            if json_tmp.exists():
                json_tmp.unlink()
            # Also remove audio file since metadata failed
            if audio_path.exists():
                audio_path.unlink()
            raise StorageError(f"Failed to write metadata JSON: {e}")
        
        return audio_path, json_path
        
    except Exception as e:
        if isinstance(e, StorageError):
            raise
        raise StorageError(f"Unexpected error during audio save: {e}")