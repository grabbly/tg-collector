#!/usr/bin/env python3
"""
ArchiveDrop - Telegram bot for archiving text and audio messages.

Usage:
    python main.py

Environment variables required:
    BOT_TOKEN - Telegram bot token from @BotFather
    STORAGE_DIR - Directory to store archived messages
    
Optional environment variables:
    RATE_LIMIT_PER_MIN - Max requests per user per minute (default: 5)  
    MAX_AUDIO_BYTES - Max audio file size in bytes (default: 10MB)
    LOG_LEVEL - Logging level (default: INFO)
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.cli.bot import main


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nBot stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
