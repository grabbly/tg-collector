# ArchiveDrop Documentation

## Overview

ArchiveDrop is a lightweight Telegram bot that collects user-submitted text and audio messages and stores them securely on a Linux server filesystem. Built with constitutional privacy-by-default principles, atomic operations, and structured logging.

## Features

- **Text Message Collection**: Stores incoming text messages as UTF-8 files
- **Audio Message Collection**: Supports voice messages in OGG, MP3, M4A, and WAV formats
- **Privacy by Default**: No personal identifiable information stored - only numeric IDs and checksums
- **Atomic Operations**: Guaranteed consistency using tmp→fsync→rename pattern
- **Rate Limiting**: Per-user throttling with configurable limits
- **Structured Logging**: JSON format for machine parsing and observability
- **Health Monitoring**: Built-in health checks with detailed diagnostics

## Installation

### Prerequisites

- Python 3.11+
- Linux server with filesystem access
- Telegram bot token from [@BotFather](https://t.me/BotFather)

### Option 1: Direct Installation

```bash
# Clone and install
git clone <repository-url>
cd tg-collector
pip install uv  # If not already installed
uv sync

# Configure environment
cp deploy/.env.template .env
# Edit .env with your bot token and settings

# Run
uv run python -m src.cli.bot
```

### Option 2: Docker

```bash
# Build image
docker build -f deploy/Dockerfile -t archive-drop .

# Run with environment file
cp deploy/.env.template .env
# Edit .env with your configuration
docker run --env-file .env -v ./storage:/app/storage archive-drop
```

### Option 3: Docker Compose

```bash
# Configure
cp deploy/.env.template .env
# Edit .env with your settings

# Deploy
docker-compose -f deploy/docker-compose.yml up -d
```

### Option 4: systemd Service (Production)

```bash
# Install application
sudo cp -r . /opt/archive-drop
sudo chown -R archive-drop:archive-drop /opt/archive-drop

# Install service
sudo cp deploy/systemd/archive-drop.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable archive-drop
sudo systemctl start archive-drop
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | Yes | - | Telegram bot token from @BotFather |
| `STORAGE_DIR` | Yes | - | Absolute path for message storage |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `RATE_LIMIT_PER_MIN` | No | `10` | Messages per user per minute |
| `MAX_AUDIO_BYTES` | No | `52428800` | Maximum audio file size (50MB default) |
| `ALLOWLIST` | No | - | Comma-separated user IDs (empty = allow all) |

### Example Configuration

```bash
# Required
BOT_TOKEN=1234567890:ABCDefGhIjKlMnOpQrStUvWxYz
STORAGE_DIR=/var/lib/archive-drop/storage

# Optional
LOG_LEVEL=INFO
RATE_LIMIT_PER_MIN=15
MAX_AUDIO_BYTES=104857600  # 100MB
ALLOWLIST=12345,67890,11111
```

## Usage

### Bot Commands

- `/start` - Show welcome message and bot information
- `/health` - Display detailed bot health and diagnostics

### Message Processing

The bot automatically processes:

1. **Text Messages**: Stored as UTF-8 `.txt` files with `.json` metadata
2. **Voice Messages**: Stored as audio files (`.ogg`, `.mp3`, etc.) with `.json` metadata

### Storage Structure

Messages are organized by date in a hierarchical structure:

```
storage/
├── 2025/
│   ├── 01/
│   │   ├── 15/
│   │   │   ├── 20250115143045-123456789-42-text.txt
│   │   │   ├── 20250115143045-123456789-42-text.json
│   │   │   ├── 20250115143102-123456789-43-audio.ogg
│   │   │   └── 20250115143102-123456789-43-audio.json
```

#### Filename Format

`{timestamp}-{chat_id}-{message_id}-{type}.{ext}`

- `timestamp`: UTC timestamp (YYYYMMDDHHMMSS)
- `chat_id`: Telegram chat ID (positive/negative number)
- `message_id`: Telegram message ID
- `type`: "text" or "audio"
- `ext`: File extension (txt, ogg, mp3, m4a, wav)

### Metadata Format

Each message includes a JSON metadata file with constitutional compliance:

```json
{
  "timestamp": "2025-01-15T14:30:45.123456",
  "message_id": 42,
  "chat_id": -1001234567890,
  "size": 1024,
  "checksum": "sha256:abcd1234...",
  "duration": 30,  // Audio only
  "mime_type": "audio/ogg"  // Audio only
}
```

**Privacy Notice**: No personal information (usernames, names, user IDs) is stored per constitutional requirements.

## Monitoring

### Health Checks

The `/health` command provides comprehensive diagnostics:

- Bot uptime and status
- Storage accessibility tests
- Session statistics (messages processed)
- Error tracking and timestamps
- Rate limiter status

### Logging

Structured JSON logs are written to stdout for collection by log aggregation systems:

```json
{
  "timestamp": "2025-01-15T14:30:45,123",
  "level": "INFO",
  "logger": "src.cli.bot", 
  "message": "Text message saved",
  "event": "text_message_saved",
  "message_id": 42,
  "chat_id": -1001234567890,
  "size": 1024,
  "checksum": "sha256:abcd1234..."
}
```

### Event Types

- **System**: `bot_starting`, `bot_shutdown`, `bot_startup_error`
- **Commands**: `command_start`, `command_health`
- **Messages**: `text_message_saved`, `voice_message_saved`
- **Errors**: `text_save_error`, `voice_save_error`, `voice_validation_error`
- **Rate limiting**: `rate_limit_exceeded`, `rate_limit_blocked`
- **Health**: `health_response_error`, `storage_check_failed`

## Architecture

### Components

```
src/
├── cli/bot.py           # Telegram bot handlers and main loop
├── config.py            # Environment configuration
├── lib/
│   ├── naming.py        # Deterministic filename generation
│   ├── rate_limit.py    # Per-user rate limiting
│   └── validation.py    # MIME type and size validation
├── services/storage.py  # Atomic filesystem operations
└── observability/
    └── logging.py       # Structured JSON logging
```

### Constitutional Principles

1. **Privacy by Default**: No PII stored, only numeric identifiers
2. **Reliability**: Atomic writes with tmp→fsync→rename pattern
3. **Transparency**: Structured logging with standard event types
4. **Security**: Input validation, rate limiting, size constraints
5. **Simplicity**: Single-responsibility modules, minimal dependencies
6. **Observability**: Health monitoring without privacy compromise
7. **Portability**: Environment-based configuration, Docker support

## Development

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test suite
uv run pytest tests/unit/
uv run pytest tests/integration/

# Run with coverage
uv run pytest --cov=src
```

### Code Quality

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type checking
uv run mypy src/
```

### Project Structure

- `tests/unit/` - Fast unit tests for individual components
- `tests/integration/` - Integration tests for component interactions
- `specs/` - Feature specifications and planning documents
- `deploy/` - Deployment configurations (Docker, systemd)

## Troubleshooting

### Common Issues

**Bot doesn't respond to messages**
- Check `BOT_TOKEN` is correct
- Verify bot is not restricted by `ALLOWLIST`
- Check rate limiting with `/health` command

**Files not being saved**
- Verify `STORAGE_DIR` exists and is writable
- Check filesystem permissions
- Review logs for error messages

**Rate limiting issues**
- Adjust `RATE_LIMIT_PER_MIN` setting
- Use `/health` to check current limits
- Consider user allowlist for trusted users

**Audio files not supported**
- Check file format is in supported list: OGG, MP3, M4A, WAV
- Verify file size under `MAX_AUDIO_BYTES` limit
- Review validation error logs

### Log Analysis

Filter logs by event type for debugging:

```bash
# Show only errors
journalctl -u archive-drop | jq 'select(.level == "ERROR")'

# Show rate limiting events
journalctl -u archive-drop | jq 'select(.event | startswith("rate_limit"))'

# Show message processing
journalctl -u archive-drop | jq 'select(.event | endswith("_saved"))'
```

### Performance Tuning

For high-volume deployments:

1. Increase `RATE_LIMIT_PER_MIN` for trusted users
2. Use SSD storage for better fsync performance
3. Monitor disk space usage regularly
4. Consider log rotation for structured logs
5. Use dedicated storage mount point

## Security Considerations

### File Permissions

- Bot runs as non-root user `archive-drop`
- Storage directory owned by bot user
- Files created with 644 permissions (readable by owner/group)

### Network Security

- Bot communicates only with Telegram API
- No incoming network ports opened
- All data transmission over HTTPS

### Data Protection

- No personal identifiers stored in filenames or metadata
- Content checksums provide integrity verification
- Atomic writes prevent partial file corruption
- Rate limiting prevents abuse

## License

[Add your license information here]

## Support

[Add support contact information here]

## Changelog

### v1.0.0 (2025-01-15)
- Initial release with constitutional governance
- Text and audio message collection
- Rate limiting and health monitoring
- Docker and systemd deployment support
- Structured JSON logging
- Comprehensive test suite
