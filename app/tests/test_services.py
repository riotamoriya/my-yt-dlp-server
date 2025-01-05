import pytest
from services.extractor import AudioExtractor  # 相対インポートを絶対インポートに変更
from fastapi import HTTPException
import os


@pytest.mark.asyncio
async def test_video_info_extraction(sample_youtube_url):
    """動画情報取得のテスト"""
    extractor = AudioExtractor()
    info = await extractor._get_video_info(sample_youtube_url)
    assert info.get('id') is not None
    assert info.get('title') is not None
    assert info.get('duration') is not None

@pytest.mark.asyncio
async def test_invalid_url_extraction(invalid_youtube_url):
    """不正なURLでの情報取得テスト"""
    extractor = AudioExtractor()
    with pytest.raises(HTTPException) as exc_info:
        await extractor._get_video_info(invalid_youtube_url)
    assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_full_extraction_process(sample_youtube_url, temp_dir):
    """完全な抽出プロセスのテスト"""
    extractor = AudioExtractor()
    result = await extractor.extract(sample_youtube_url)
    
    assert 'video_id' in result
    assert 'title' in result
    assert 'duration' in result
    assert 'file_path' in result
    
    # ファイルが実際に生成されているか確認
    assert os.path.exists(result['file_path'])
    assert os.path.getsize(result['file_path']) > 0