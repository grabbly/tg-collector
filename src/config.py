"""
Configuration management for ArchiveDrop bot.

Loads and validates environment variables with safe defaults.
Required vars: BOT_TOKEN, STORAGE_DIR
Optional vars: RATE_LIMIT_PER_MIN, MAX_AUDIO_BYTES, ALLOWLIST, LOG_LEVEL
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv


class Config:
    """Configuration container with validation."""
    
    def __init__(self) -> None:
        # Load .env file if it exists
        load_dotenv()
        
        # Required settings
        self.bot_token = self._get_required_str("BOT_TOKEN")
        self.storage_dir = Path(self._get_required_str("STORAGE_DIR"))
        
        # Optional settings with defaults
        self.rate_limit_per_min = int(os.getenv("RATE_LIMIT_PER_MIN", "10"))
        self.max_audio_bytes = int(os.getenv("MAX_AUDIO_BYTES", "52428800"))  # 50MB
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Parse allowlist (comma-separated user IDs)
        allowlist_str = os.getenv("ALLOWLIST", "")
        self.allowlist: Optional[List[int]] = None
        if allowlist_str.strip():
            try:
                self.allowlist = [int(uid.strip()) for uid in allowlist_str.split(",")]
            except ValueError as e:
                raise ValueError(f"Invalid ALLOWLIST format: {e}")
        
        # Validation
        self._validate()
    
    def _get_required_str(self, key: str) -> str:
        """Get a required environment variable."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def _validate(self) -> None:
        """Validate configuration values."""
        if not self.storage_dir.is_absolute():
            raise ValueError("STORAGE_DIR must be an absolute path")
        
        if self.rate_limit_per_min < 1:
            raise ValueError("RATE_LIMIT_PER_MIN must be at least 1")
        
        if self.max_audio_bytes < 1024:  # At least 1KB
            raise ValueError("MAX_AUDIO_BYTES must be at least 1024 bytes")
        
        if self.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"Invalid LOG_LEVEL: {self.log_level}")
    
    def is_user_allowed(self, user_id: int) -> bool:
        """Check if a user ID is in the allowlist (if configured)."""
        if self.allowlist is None:
            return True  # No allowlist means everyone is allowed
        return user_id in self.allowlist
    
    def get_redacted_summary(self) -> dict:
        """Get configuration summary with sensitive values redacted."""
        return {
            "bot_token_length": len(self.bot_token) if self.bot_token else 0,
            "storage_dir": str(self.storage_dir),
            "rate_limit_per_min": self.rate_limit_per_min,
            "max_audio_bytes": self.max_audio_bytes,
            "log_level": self.log_level,
            "allowlist_count": len(self.allowlist) if self.allowlist else None,
        }


# Create global config instance - only when imported as main module
# Tests should create their own Config instances or use mocks
config = None

def get_config() -> Config:
    """Get global config instance, creating it if needed."""
    global config
    if config is None:
        config = Config()
    return config