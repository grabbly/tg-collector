"""
Structured JSON logging for ArchiveDrop.

Implements constitutional transparency requirements:
- JSON structured format for machine parsing  
- Never logs raw message content (privacy by default)
- Includes message metadata for correlation
- Size and checksum references only
- Consistent field naming and event types

JSON LOG SCHEMA (finalized):
{
    "timestamp": "2025-01-15T14:30:45,123",  // ISO format with milliseconds
    "level": "INFO|ERROR|WARNING|DEBUG",     // Python logging levels
    "logger": "src.cli.bot",                 // Logger name (module path)
    "message": "Human readable message",     // Brief description
    "event": "message_saved|rate_limit_exceeded|...",  // Event type (see EVENT_TYPES)
    "message_type": "text|audio",            // Optional: type of Telegram message
    "message_id": 12345,                     // Optional: Telegram message ID
    "chat_id": -1001234567890,              // Optional: Telegram chat ID
    "status": "success|error|rejected",      // Optional: operation result
    "size": 1024,                           // Optional: content size in bytes
    "checksum": "sha256hash...",            // Optional: SHA256 content checksum
    "details": {...}                        // Optional: additional structured data
}

EVENT TYPES (stable):
- System: bot_starting, bot_shutdown, bot_startup_error
- Commands: command_start, command_health
- Messages: text_message_saved, voice_message_saved
- Errors: text_save_error, voice_save_error, voice_validation_error
- Rate limiting: rate_limit_exceeded, rate_limit_blocked
- Health: health_response_error, storage_check_failed

PRIVACY COMPLIANCE:
- NEVER include raw message text or audio data
- Use size/checksum for content identification
- Numeric IDs only (chat_id, message_id, sender_id)
- No usernames, display names, or personal data
"""

import json
import logging
import sys
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """JSON log formatter with constitutional compliance."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with required fields."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        
        # Add structured fields if present
        if hasattr(record, "event"):
            log_data["event"] = record.event
        if hasattr(record, "message_type"):
            log_data["message_type"] = record.message_type  
        if hasattr(record, "message_id"):
            log_data["message_id"] = record.message_id
        if hasattr(record, "chat_id"):
            log_data["chat_id"] = record.chat_id
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "size"):
            log_data["size"] = record.size
        if hasattr(record, "checksum"):
            log_data["checksum"] = record.checksum
        if hasattr(record, "details") and record.details:
            log_data["details"] = record.details
            
        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with JSON formatting."""
    logger = logging.getLogger(name)
    
    # Only add handler if none exists (avoid duplicates)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    
    return logger


def log_event(
    logger: logging.Logger,
    event: str,
    level: int = logging.INFO,
    message: str = "",
    *,
    message_type: Optional[str] = None,
    message_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    status: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    size: Optional[int] = None,
    checksum: Optional[str] = None,
) -> None:
    """
    Log a structured event with consistent fields.
    
    NEVER pass raw message text or audio content to this function.
    Use size/checksum for content references instead.
    """
    # Create log record with extra fields
    extra = {
        "event": event,
        "message_type": message_type,
        "message_id": message_id,
        "chat_id": chat_id,
        "status": status,
        "details": details,
        "size": size,
        "checksum": checksum
    }
    
    # Remove None values
    extra = {k: v for k, v in extra.items() if v is not None}
    
    logger.log(level, message, extra=extra)


# Error code mappings for consistent error handling
ERROR_CODES = {
    # Storage errors
    "storage_disk_full": "E001",
    "storage_permission_denied": "E002", 
    "storage_directory_missing": "E003",
    "storage_atomic_write_failed": "E004",
    
    # Validation errors
    "invalid_mime_type": "E101",
    "file_too_large": "E102",
    "file_corrupted": "E103",
    "unsupported_format": "E104",
    
    # Rate limiting
    "rate_limit_exceeded": "E201",
    "quota_exhausted": "E202",
    
    # Bot/Telegram errors  
    "telegram_api_error": "E301",
    "network_timeout": "E302",
    "authentication_failed": "E303",
    "message_too_old": "E304",
    
    # Configuration errors
    "missing_config": "E401",
    "invalid_config": "E402",
    
    # System errors
    "out_of_memory": "E501",
    "disk_space_low": "E502",
    "system_overload": "E503"
}


def get_error_code(error_type: str) -> str:
    """Get standardized error code for error type."""
    return ERROR_CODES.get(error_type, "E999")  # E999 = unknown error


def log_error_with_code(
    logger: logging.Logger,
    error_type: str,
    message: str,
    *,
    exception: Optional[Exception] = None,
    chat_id: Optional[int] = None,
    message_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with standardized error code.
    
    Args:
        logger: Logger instance
        error_type: Type of error (key in ERROR_CODES)
        message: Human-readable error message
        exception: Optional exception that caused the error
        chat_id: Optional chat ID for context
        message_id: Optional message ID for context  
        details: Optional additional details (no sensitive data)
    """
    error_code = get_error_code(error_type)
    
    error_details = {"error_code": error_code}
    if exception:
        error_details["exception_type"] = type(exception).__name__
        error_details["exception_message"] = str(exception)
    if details:
        error_details.update(details)
    
    log_event(
        logger=logger,
        event=error_type,
        level=logging.ERROR,
        message=f"[{error_code}] {message}",
        chat_id=chat_id,
        message_id=message_id,
        status="error",
        details=error_details
    )

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter for structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": getattr(record, "event", "unknown"),
            "message": record.getMessage(),
        }

        # Add optional fields if present
        for field in ["type", "message_id", "chat_id", "status", "details", "size", "checksum"]:
            if hasattr(record, field) and getattr(record, field) is not None:
                log_entry[field] = getattr(record, field)

        return json.dumps(log_entry)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with JSON formatting."""
    logger = logging.getLogger(name)
    
    # Only add handler if none exists (avoid duplicates)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    
    return logger


def log_event(
    logger: logging.Logger,
    event: str,
    level: int = logging.INFO,
    message: str = "",
    *,
    message_type: Optional[str] = None,
    message_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    status: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    size: Optional[int] = None,
    checksum: Optional[str] = None,
) -> None:
    """
    Log a structured event with consistent fields.
    
    NEVER pass raw message text or audio content to this function.
    Use size/checksum for content references instead.
    """
    extra = {
        "event": event,
        "type": message_type,
        "message_id": message_id,
        "chat_id": chat_id,
        "status": status,
        "details": details,
        "size": size,
        "checksum": checksum,
    }
    
    # Remove None values
    extra = {k: v for k, v in extra.items() if v is not None}
    
    logger.log(level, message, extra=extra)