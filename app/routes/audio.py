from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from services.extractor import AudioExtractor
from utils.file_handler import cleanup_temp_file
import logging
from urllib.parse import quote  # これを追加


logger = logging.getLogger(__name__)
router = APIRouter()

class AudioExtractionRequest(BaseModel):
    url: HttpUrl


@router.post("/extract-audio")
async def extract_audio(request: AudioExtractionRequest):
    try:
        extractor = AudioExtractor()
        result = await extractor.extract(str(request.url))
        
        # ファイル名を適切にエンコード
        filename = result["filename"]
        encoded_filename = quote(filename)
        
        response = FileResponse(
            path=result["file_path"],
            media_type="audio/mpeg",
            filename=filename  # オリジナルのファイル名
        )
        
        # Content-Dispositionヘッダーを明示的に設定
        response.headers["Content-Disposition"] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
        
        response.background = lambda: cleanup_temp_file(result["file_path"])
        
        return response

    except HTTPException as he:
        logger.error(f"HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))