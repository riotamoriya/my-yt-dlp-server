import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

async def cleanup_temp_file(file_path: Optional[str]) -> None:
    """一時ファイルを削除"""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")

def get_file_size(file_path: str) -> int:
    """ファイルサイズを取得（バイト）"""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size: {str(e)}")
        return 0