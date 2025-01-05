from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from services.extractor import AudioExtractor
from utils.file_handler import cleanup_temp_file
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class AudioExtractionRequest(BaseModel):
    url: HttpUrl

@router.post("/extract-audio")
async def extract_audio(request: AudioExtractionRequest):
    try:
        extractor = AudioExtractor()
        result = await extractor.extract(str(request.url))
        
        response = FileResponse(
            result["file_path"],
            media_type="audio/mpeg",
            filename=f"{result['video_id']}.mp3"
        )
        
        response.background = lambda: cleanup_temp_file(result["file_path"])
        
        return response

    except HTTPException as he:
        # HTTPExceptionを上位に伝播
        raise he
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))