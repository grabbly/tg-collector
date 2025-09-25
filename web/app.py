#!/usr/bin/env python3
"""
ArchiveDrop Web Interface
Provides web-based access to collected messages and audio files.
"""

import os
import re
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from flask import Flask, render_template, request, jsonify, send_file, abort, session, redirect, url_for
import mimetypes

app = Flask(__name__)

# Configuration
STORAGE_DIR = os.environ.get('STORAGE_DIR', '/opt/tg-collector/storage')
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
PIN_CODE = os.environ.get('PIN_CODE', '1234')  # Default PIN, change via environment
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-secret-key-in-production')

app.secret_key = SECRET_KEY

# Rate limiting for PIN attempts
failed_attempts = {}
LOCKOUT_TIME = 300  # 5 minutes lockout
MAX_ATTEMPTS = 3


def check_ip_lockout(client_ip):
    """Check if IP is locked out due to too many failed attempts"""
    if client_ip in failed_attempts:
        attempts, last_attempt = failed_attempts[client_ip]
        if attempts >= MAX_ATTEMPTS:
            if datetime.now() - last_attempt < timedelta(seconds=LOCKOUT_TIME):
                return True
            else:
                # Lockout expired, reset attempts
                del failed_attempts[client_ip]
    return False

def record_failed_attempt(client_ip):
    """Record a failed login attempt"""
    now = datetime.now()
    if client_ip in failed_attempts:
        attempts, _ = failed_attempts[client_ip]
        failed_attempts[client_ip] = (attempts + 1, now)
    else:
        failed_attempts[client_ip] = (1, now)

def require_auth():
    """Check if user is authenticated, redirect to login if not"""
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with PIN code"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    # Check if IP is locked out
    if check_ip_lockout(client_ip):
        remaining = LOCKOUT_TIME - (datetime.now() - failed_attempts[client_ip][1]).seconds
        return render_template('login.html', 
                             error=f'Too many failed attempts. Try again in {remaining} seconds.',
                             lockout=True), 429
    
    if request.method == 'POST':
        pin = request.form.get('pin', '').strip()
        
        if pin == PIN_CODE:
            # Successful login
            session['authenticated'] = True
            session.permanent = True
            app.permanent_session_lifetime = timedelta(hours=24)  # 24 hour session
            
            # Clear failed attempts for this IP
            if client_ip in failed_attempts:
                del failed_attempts[client_ip]
                
            return redirect(url_for('index'))
        else:
            # Failed login
            record_failed_attempt(client_ip)
            attempts_left = MAX_ATTEMPTS - failed_attempts[client_ip][0]
            
            if attempts_left <= 0:
                return render_template('login.html', 
                                     error=f'Too many failed attempts. Locked out for {LOCKOUT_TIME//60} minutes.',
                                     lockout=True), 429
            else:
                return render_template('login.html', 
                                     error=f'Wrong PIN. {attempts_left} attempts remaining.'), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))


@app.after_request
def add_no_cache_headers(response):
    """Disable caching for HTML to prevent stale UI in proxies/browsers."""
    content_type = response.headers.get('Content-Type', '')
    if 'text/html' in content_type:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

def parse_filename(filename: str) -> Optional[Dict]:
    """Parse ArchiveDrop filename into components (supports 20250925150427-356747848-11-text.txt)."""
    # Pattern: YYYYMMDDHHMMSS-USERID-SEQ-TYPE.txt
    pattern = r'^(\d{14})-(\d+)-(\d+)-(text|audio)\.(.+)$'
    match = re.match(pattern, filename)
    if not match:
        return None
    dt_str, user_id, seq, msg_type, ext = match.groups()
    try:
        dt = datetime.strptime(dt_str, "%Y%m%d%H%M%S")
    except Exception:
        return None
    return {
        'filename': filename,
        'datetime': dt,
        'date': dt_str[:8],
        'time': dt_str[8:],
        'type': msg_type,
        'user_id': user_id,
        'seq': seq,
        'extension': ext,
        'size': get_file_size(filename)
    }

def get_file_size(filename: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(os.path.join(STORAGE_DIR, filename))
    except OSError:
        return 0

def scan_files(
    date_filter: Optional[str] = None,
    type_filter: Optional[str] = None,
    search_query: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    """Recursively scan storage directory and aggregate primary files.

    For text: prefer .txt over .json metadata.
    For audio: prefer media files (.ogg/.mp3/.m4a/.wav) over .json metadata.
    """
    media_exts = {"ogg", "mp3", "m4a", "wav"}
    aggregated: Dict[str, Dict] = {}
    try:
        storage_path = Path(STORAGE_DIR)
        if not storage_path.exists():
            return []
        # Recursively walk through all files
        for filepath in storage_path.rglob('*'):
            if not filepath.is_file():
                continue
            file_info = parse_filename(filepath.name)
            if not file_info:
                continue
            # Ensure size is taken from the actual path (handles nested dirs)
            try:
                file_info['size'] = filepath.stat().st_size
            except Exception:
                pass
            # Keep relative path for nested directories
            try:
                file_info['relpath'] = str(filepath.relative_to(storage_path).as_posix())
            except Exception:
                file_info['relpath'] = filepath.name
            # Group by base name without extension (includes -text/-audio)
            base_key = filepath.stem  # e.g., 20250925145342-356747848-8-audio

            # Apply basic pre-filters before aggregation when possible
            if date_filter and file_info['date'] != date_filter:
                continue
            if type_filter and file_info['type'] != type_filter:
                continue
            # Search in text files content only
            if search_query and file_info['type'] == 'text':
                try:
                    content = filepath.read_text(encoding='utf-8')
                    if search_query.lower() not in content.lower():
                        continue
                except Exception:
                    continue

            existing = aggregated.get(base_key)
            ext = file_info['extension'].lower()
            is_media = file_info['type'] == 'audio' and ext in media_exts
            is_text_primary = file_info['type'] == 'text' and ext == 'txt'
            is_json_meta = ext == 'json'

            if existing is None:
                # Initialize entry; we'll set primary relpath below
                entry = dict(file_info)
                entry['meta_relpath'] = None
                # Only initialize with non-JSON files as primary
                if is_media or is_text_primary:
                    # Primary file - keep as is
                    pass
                elif is_json_meta:
                    # JSON meta as placeholder; primary may be updated later
                    entry['filename'] = None  # Will be set when primary found
                    entry['relpath'] = None
                    entry['extension'] = None
                    entry['size'] = 0
                aggregated[base_key] = entry
                existing = entry

            # Update primary/metadata preferences
            if file_info['type'] == 'audio':
                if is_media:
                    # Prefer media as primary
                    existing.update({
                        'filename': file_info['filename'],
                        'relpath': file_info['relpath'],
                        'extension': file_info['extension'],
                        'size': file_info['size'],
                    })
                elif is_json_meta:
                    existing['meta_relpath'] = file_info['relpath']
            else:  # text
                if is_text_primary:
                    # Prefer .txt as primary
                    existing.update({
                        'filename': file_info['filename'],
                        'relpath': file_info['relpath'],
                        'extension': file_info['extension'],
                        'size': file_info['size'],
                    })
                elif is_json_meta:
                    existing['meta_relpath'] = file_info['relpath']
            # (Old list-based accumulation removed; aggregation is used instead)
    except Exception as e:
        print(f"Error scanning files: {e}")
    # Turn into list and sort by datetime descending
    files_list = list(aggregated.values())
    # Drop entries that only have JSON metadata but no primary file, or have None filename
    files_list = [f for f in files_list if f.get('relpath') and f.get('filename') and f.get('extension', '').lower() != 'json']
    files_list.sort(key=lambda x: x['datetime'], reverse=True)
    # Enforce limit
    return files_list[:limit]

@app.route('/')
def index():
    """Main page with file listing and search."""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    return render_template('index.html')

@app.route('/api/files')
def api_files():
    """API endpoint to get files with filtering."""
    auth_check = require_auth()
    if auth_check:
        return auth_check
        
    date_filter = request.args.get('date')
    type_filter = request.args.get('type')
    search_query = request.args.get('search')
    limit = min(int(request.args.get('limit', 100)), 500)
    
    files = scan_files(date_filter, type_filter, search_query, limit)

    # Convert datetime objects to strings for JSON serialization
    for file_info in files:
        # Keep ISO for programmatic use and a pretty string for display
        dt_obj = file_info.get('datetime')
        if isinstance(dt_obj, datetime):
            file_info['datetime'] = dt_obj.isoformat()
            file_info['datetime_str'] = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        # Do not keep raw datetime objects in JSON
        if isinstance(file_info.get('datetime'), datetime):
            file_info['datetime'] = file_info['datetime'].isoformat()

    return jsonify({
        'files': files,
        'total': len(files)
    })

@app.route('/api/content/<path:filename>')
def api_content(filename):
    """Get file content for text-like files by relative path."""
    auth_check = require_auth()
    if auth_check:
        return auth_check
        
    filepath = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)

    # Basic extension check for text content
    _, ext = os.path.splitext(filepath.lower())
    text_exts = {'.txt', '.json', '.log', '.md'}
    if ext not in text_exts:
        abort(400)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception:
        abort(500)

@app.route('/api/download/<path:filename>')
def api_download(filename):
    """Download file by relative path."""
    auth_check = require_auth()
    if auth_check:
        return auth_check
        
    filepath = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)
    mimetype = mimetypes.guess_type(filepath)[0]
    return send_file(filepath, as_attachment=True, mimetype=mimetype)

# Backward/alternate route aliases to match frontend
@app.route('/api/file/<path:filename>')
def api_file_alias(filename):
    auth_check = require_auth()
    if auth_check:
        return auth_check
    return api_content(filename)

@app.route('/download/<path:filename>')
def download_alias(filename):
    auth_check = require_auth()
    if auth_check:
        return auth_check
    return api_download(filename)

# Inline media streaming (useful for audio preview)
@app.route('/media/<path:filename>')
def media_stream(filename):
    auth_check = require_auth()
    if auth_check:
        return auth_check
        
    filepath = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)
    mimetype = mimetypes.guess_type(filepath)[0]
    return send_file(filepath, as_attachment=False, mimetype=mimetype)

@app.route('/api/stats')
def api_stats():
    """Get storage statistics."""
    auth_check = require_auth()
    if auth_check:
        return auth_check
        
    try:
        files = scan_files(limit=10000)  # Get more files for stats

        stats = {
            'total_files': len(files),
            'text_files': len([f for f in files if f['type'] == 'text']),
            'audio_files': len([f for f in files if f['type'] == 'audio']),
            'total_size': sum(f['size'] for f in files),
            'date_range': {
                'first': files[-1]['datetime'].strftime('%Y-%m-%d %H:%M:%S') if files else None,
                'last': files[0]['datetime'].strftime('%Y-%m-%d %H:%M:%S') if files else None
            }
        }
        
        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_files = [f for f in files if f['datetime'] > week_ago]
        stats['recent_activity'] = len(recent_files)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)