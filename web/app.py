#!/usr/bin/env python3
"""
ArchiveDrop Web Interface
Provides web-based access to collected messages and audio files.
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from flask import Flask, render_template, request, jsonify, send_file, abort
import mimetypes

app = Flask(__name__)

# Configuration
STORAGE_DIR = os.environ.get('STORAGE_DIR', '/opt/tg-collector/storage')
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

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

def scan_files(date_filter: Optional[str] = None, 
               type_filter: Optional[str] = None,
               search_query: Optional[str] = None,
               limit: int = 100) -> List[Dict]:
    """Recursively scan storage directory for files matching criteria."""
    files = []
    try:
        storage_path = Path(STORAGE_DIR)
        if not storage_path.exists():
            return files
        # Recursively walk through all files
        for filepath in storage_path.rglob('*'):
            if not filepath.is_file():
                continue
            file_info = parse_filename(filepath.name)
            if not file_info:
                continue
            # Apply filters
            if date_filter and file_info['date'] != date_filter:
                continue
            if type_filter and file_info['type'] != type_filter:
                continue
            # Search in text files content
            if search_query and file_info['type'] == 'text':
                try:
                    content = filepath.read_text(encoding='utf-8')
                    if search_query.lower() not in content.lower():
                        continue
                except:
                    continue
            files.append(file_info)
            if len(files) >= limit:
                break
    except Exception as e:
        print(f"Error scanning files: {e}")
    # Sort by datetime descending
    files.sort(key=lambda x: x['datetime'], reverse=True)
    return files

@app.route('/')
def index():
    """Main page with file listing and search."""
    return render_template('index.html')

@app.route('/api/files')
def api_files():
    """API endpoint to get files with filtering."""
    date_filter = request.args.get('date')
    type_filter = request.args.get('type')
    search_query = request.args.get('search')
    limit = min(int(request.args.get('limit', 100)), 500)
    
    files = scan_files(date_filter, type_filter, search_query, limit)
    
    # Convert datetime objects to strings for JSON serialization
    for file_info in files:
        file_info['datetime_str'] = file_info['datetime'].strftime('%Y-%m-%d %H:%M:%S')
        del file_info['datetime']
    
    return jsonify({
        'files': files,
        'total': len(files)
    })

@app.route('/api/content/<filename>')
def api_content(filename):
    """Get file content (text files only)."""
    file_info = parse_filename(filename)
    if not file_info or file_info['type'] != 'text':
        abort(400)
        
    filepath = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        abort(500)

@app.route('/api/download/<filename>')
def api_download(filename):
    """Download file."""
    file_info = parse_filename(filename)
    if not file_info:
        abort(400)
        
    filepath = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)
        
    mimetype = mimetypes.guess_type(filepath)[0]
    return send_file(filepath, as_attachment=True, mimetype=mimetype)

@app.route('/api/stats')
def api_stats():
    """Get storage statistics."""
    try:
        files = scan_files(limit=10000)  # Get more files for stats
        
        stats = {
            'total_files': len(files),
            'text_files': len([f for f in files if f['type'] == 'text']),
            'audio_files': len([f for f in files if f['type'] == 'audio']),
            'total_size': sum(f['size'] for f in files),
            'date_range': {
                'first': files[-1]['datetime_str'] if files else None,
                'last': files[0]['datetime_str'] if files else None
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