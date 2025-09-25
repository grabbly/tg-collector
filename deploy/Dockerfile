# Multi-stage build for ArchiveDrop Telegram bot
FROM python:3.11-slim AS builder

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies into virtual environment
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.11-slim AS production

# Create non-root user for security
RUN groupadd -r archive-drop && \
    useradd -r -g archive-drop -d /app -s /bin/bash archive-drop

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=archive-drop:archive-drop /app/.venv /app/.venv

# Copy application code
COPY --chown=archive-drop:archive-drop src/ src/
COPY --chown=archive-drop:archive-drop main.py ./

# Create storage directory
RUN mkdir -p /app/storage && \
    chown archive-drop:archive-drop /app/storage

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV STORAGE_ROOT="/app/storage"

# Switch to non-root user
USER archive-drop

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Expose port (if webhook mode is added later)
EXPOSE 8080

# Run the bot
CMD ["python", "-m", "src.cli.bot"]