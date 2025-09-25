import os
import tempfile
import pytest
from flask import Flask
from web.app import app as flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'ArchiveDrop Web Interface' in response.data

def test_api_files_empty(client):
    response = client.get('/api/files')
    assert response.status_code == 200
    data = response.get_json()
    assert 'files' in data
    assert isinstance(data['files'], list)

# You can add more tests for /api/content/<filename> and /api/download/<filename> if needed.
