from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from services.extractor import AudioExtractor
from utils.file_handler import cleanup_temp_file
import logging
# import yt_dlp
import os  # これを追加

logger = logging.getLogger(__name__)
router = APIRouter()

class AudioExtractionRequest(BaseModel):
    url: HttpUrl

@router.post("/extract-audio")
async def extract_audio(request: AudioExtractionRequest):
    try:
        extractor = AudioExtractor()
        
        # URLの基本的なバリデーション
        if not extractor._is_valid_youtube_url(str(request.url)):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL format")
            
        result = await extractor.extract(str(request.url))
        
        # ファイルの存在確認
        if not os.path.exists(result["file_path"]):
            raise HTTPException(status_code=400, detail="File conversion failed")
        
        response = FileResponse(
            result["file_path"],
            media_type="audio/mpeg",
            filename=result["filename"]
        )
        
        response.background = lambda: cleanup_temp_file(result["file_path"])
        
        return response

    except HTTPException as he:
        # エラーログを追加
        logger.error(f"HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))