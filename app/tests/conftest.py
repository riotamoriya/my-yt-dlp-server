import pytest
from fastapi.testclient import TestClient
from ..main import app
import os

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_youtube_url():
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

@pytest.fixture
def invalid_youtube_url():
    return "https://www.youtube.com/invalid"

@pytest.fixture
def temp_dir():
    """テスト用の一時ディレクトリを準備"""
    test_temp_dir = "test_temp"
    os.makedirs(test_temp_dir, exist_ok=True)
    yield test_temp_dir
    # テスト後にクリーンアップ
    for file in os.listdir(test_temp_dir):
        os.remove(os.path.join(test_temp_dir, file))
    os.rmdir(test_temp_dir)