import pytest
import os
from utils.file_handler import cleanup_temp_file, get_file_size  # 相対インポートを絶対インポートに変更

@pytest.mark.asyncio
async def test_cleanup_temp_file(temp_dir):
    """一時ファイルのクリーンアップテスト"""
    # テストファイルを作成
    test_file = os.path.join(temp_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("test content")
    
    assert os.path.exists(test_file)
    await cleanup_temp_file(test_file)
    assert not os.path.exists(test_file)

def test_get_file_size(temp_dir):
    """ファイルサイズ取得テスト"""
    test_file = os.path.join(temp_dir, "test.txt")
    content = "test content"
    
    with open(test_file, "w") as f:
        f.write(content)
    
    size = get_file_size(test_file)
    assert size == len(content)

def test_get_file_size_nonexistent():
    """存在しないファイルのサイズ取得テスト"""
    size = get_file_size("nonexistent.txt")
    assert size == 0