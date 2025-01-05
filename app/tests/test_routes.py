import pytest
from fastapi.testclient import TestClient
from ..main import app

def test_health_check(client):
    """ヘルスチェックエンドポイントのテスト"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_extract_audio_invalid_url_format(client):
    """不正なURL形式のテスト"""
    response = client.post(
        "/api/v1/extract-audio",
        json={"url": "not_a_url"}
    )
    assert response.status_code == 422


def test_extract_audio_nonexistent_video(client, invalid_youtube_url):
    """存在しない動画URLのテスト"""
    response = client.post(
        "/api/v1/extract-audio",
        json={"url": invalid_youtube_url}
    )
    assert response.status_code == 400

def test_extract_audio_success(client, sample_youtube_url):
    """正常系のテスト"""
    response = client.post(
        "/api/v1/extract-audio",
        json={"url": sample_youtube_url}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"