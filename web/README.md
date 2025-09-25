# ArchiveDrop Web Interface Deployment

## Overview
The web interface provides a user-friendly way to browse, search, and download archived messages and audio files collected by the ArchiveDrop bot.

## Features
- **File Browser**: View all collected files with metadata
- **Search & Filter**: Filter by date, type (text/audio), and search text content
- **Content Preview**: View text message content inline
- **Download**: Download individual files
- **Statistics**: Overview of total files, sizes, and recent activity
- **Responsive Design**: Works on desktop and mobile devices

## Deployment Steps

### 1. Build and Start Services
```bash
# Build both bot and web interface
docker compose -f /opt/tg-collector/deploy/docker-compose.yml build

# Start services
docker compose -f /opt/tg-collector/deploy/docker-compose.yml up -d

# Check that web interface is running
curl http://localhost:5000/api/stats
```

### 2. Set Up Nginx (for subdomain access)
```bash
# Copy nginx configuration
sudo cp /opt/tg-collector/deploy/nginx-archive.conf /etc/nginx/sites-available/

# Edit the configuration
sudo nano /etc/nginx/sites-available/nginx-archive.conf
# Update server_name to your subdomain (e.g., archive.yourdomain.com)

# Enable the site
sudo ln -s /etc/nginx/sites-available/nginx-archive.conf /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 3. DNS Configuration
Point your subdomain to your server's IP address:
```
archive.yourdomain.com A 91.200.41.59
```

### 4. SSL Certificate (Optional but Recommended)
```bash
# Install certbot if not already installed
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d archive.yourdomain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

## API Endpoints

- `GET /` - Main web interface
- `GET /api/files` - List files with optional filters
  - `?date=YYYYMMDD` - Filter by date
  - `?type=text|audio` - Filter by type  
  - `?search=query` - Search in text content
  - `?limit=N` - Limit results
- `GET /api/content/<filename>` - Get text file content
- `GET /api/download/<filename>` - Download file
- `GET /api/stats` - Storage statistics

## Security Considerations

- Web interface has **read-only** access to storage
- Rate limiting configured in Nginx
- Security headers enabled
- Files are served with appropriate MIME types
- No authentication required (consider adding if needed)

## Troubleshooting

### Web Interface Not Starting
```bash
# Check logs
docker logs archive-drop-web

# Check if port 5000 is available
sudo netstat -tlnp | grep :5000
```

### Nginx Issues
```bash
# Check nginx logs
sudo tail -f /var/log/nginx/archive_error.log

# Test configuration
sudo nginx -t
```

### Files Not Showing
- Verify storage directory permissions: `ls -la /opt/tg-collector/storage`
- Check if bot is saving files correctly
- Ensure web container has read access to storage

## Development

To run locally for development:
```bash
cd web
pip install -r requirements.txt
export STORAGE_DIR=/path/to/storage
export DEBUG=true
python app.py
```

Open http://localhost:5000 in your browser.