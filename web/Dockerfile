# Multi-stage build for ArchiveDrop Web Interface
FROM python:3.11-slim AS web-interface

# Create non-root user
RUN groupadd -r webuser && \
    useradd -r -g webuser -d /app -s /bin/bash webuser

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy web application
COPY --chown=webuser:webuser web/ .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV STORAGE_DIR=/app/storage

# Switch to non-root user
USER webuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/stats || exit 1

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "30", "app:app"]