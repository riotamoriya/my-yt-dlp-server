# from fastapi import APIRouter, HTTPException
# from fastapi.responses import FileResponse
# from pydantic import BaseModel, HttpUrl
# from services.extractor import AudioExtractor
# from utils.file_handler import cleanup_temp_file
# import logging
# from urllib.parse import quote  # これを追加


import zipfile
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
import logging
from services.extractor import AudioExtractor
from utils.file_handler import cleanup_temp_file


logger = logging.getLogger(__name__)
router = APIRouter()

class AudioExtractionRequest(BaseModel):
    url: HttpUrl


@router.post("/extract-audio")
async def extract_audio(request: AudioExtractionRequest):
    try:
        extractor = AudioExtractor()
        
        # プレイリストかどうかをチェック
        if await extractor.is_playlist(str(request.url)):
            logger.info("Playlist URL detected, processing as playlist")
            result = await extract_playlist_with_folder(extractor, str(request.url))
            return result
        else:
            logger.info("Single video URL detected")
            result = await extractor.extract(str(request.url))
            
            response = FileResponse(
                result["file_path"],
                media_type="audio/mpeg",
                filename=result["filename"]
            )
            response.background = lambda: cleanup_temp_file(result["file_path"])
            return response

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


async def extract_playlist_with_folder(extractor: AudioExtractor, url: str):
    try:
        playlist_info = await extractor.get_playlist_info(url)
        playlist_title = playlist_info.get('title', 'Unknown_Playlist')
        safe_playlist_title = "".join(c for c in playlist_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        logger.info(f"Processing playlist: {playlist_title}")
        
        # プレイリスト用のフォルダを作成
        playlist_dir = os.path.join(extractor.temp_dir, safe_playlist_title)
        os.makedirs(playlist_dir, exist_ok=True)
        
        # 各動画を処理
        results = []
        total_videos = len(playlist_info['entries'])
        logger.info(f"Found {total_videos} videos in playlist")
        
        for i, video in enumerate(playlist_info['entries'], 1):
            try:
                video_url = f"https://www.youtube.com/watch?v={video['id']}"
                logger.info(f"Processing video {i}/{total_videos}: {video.get('title', 'Unknown')}")
                
                result = await extractor.extract(video_url, playlist_dir)
                results.append({
                    "success": True,
                    "title": result['title'],
                    "filename": result['filename']
                })
            except Exception as e:
                logger.error(f"Error processing video: {str(e)}")
                results.append({
                    "success": False,
                    "title": video.get('title', 'Unknown'),
                    "error": str(e)
                })

        # ZIPファイルの作成
        zip_path = f"{playlist_dir}.zip"
        logger.info(f"Creating ZIP file: {zip_path}")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in os.listdir(playlist_dir):
                file_path = os.path.join(playlist_dir, file)
                zipf.write(file_path, os.path.basename(file_path))

        return FileResponse(
            zip_path,
            media_type='application/zip',
            filename=f"{safe_playlist_title}.zip"
        )
    except Exception as e:
        logger.error(f"Error in playlist processing: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    


class PlaylistExtractionRequest(BaseModel):
    url: HttpUrl
    
@router.post("/extract-playlist")


async def extract_playlist(request: PlaylistExtractionRequest):
    try:
        extractor = AudioExtractor()
        logger.info(f"Processing URL: {request.url}")
        
        # プレイリスト情報の取得
        playlist_info = await extractor.get_playlist_info(str(request.url))
        if not playlist_info:
            raise HTTPException(status_code=400, detail="Could not retrieve playlist information")

        logger.info(f"Processing playlist with {len(playlist_info.get('entries', []))} videos")
        
        
        # 各動画を処理
        results = []
        for video in playlist_info['entries']:
            try:
                video_url = f"https://www.youtube.com/watch?v={video['id']}"
                result = await extractor.extract(video_url)
                results.append({
                    "success": True,
                    "video_id": video['id'],
                    "title": result['title'],
                    "filename": result['filename']
                })
            except Exception as e:
                results.append({
                    "success": False,
                    "video_id": video['id'],
                    "error": str(e)
                })
        
        return {
            "playlist_title": playlist_info.get('title'),
            "total_videos": len(playlist_info['entries']),
            "results": results
        }

    except HTTPException as he:
        raise he
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))