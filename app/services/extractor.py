import yt_dlp
import os
import asyncio
import logging
from typing import Dict
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class AudioExtractor:
    def __init__(self):
        self.temp_dir = "temp"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'outtmpl': f'{self.temp_dir}/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

    async def extract(self, url: str) -> Dict:
        """
        YouTubeのURLから音声を抽出してMP3として保存
        
        Args:
            url (str): YouTubeのURL
            
        Returns:
            Dict: 抽出した音声ファイルの情報
            
        Raises:
            HTTPException: 処理中にエラーが発生した場合
        """
        try:
            # URLの情報を取得
            info = await self._get_video_info(url)
            video_id = info.get('id')
            if not video_id:
                raise HTTPException(status_code=400, detail="Could not extract video ID")

            # 音声を抽出
            output_file = await self._download_and_convert(url, video_id)
            
            # ファイル情報を返す
            return {
                "video_id": video_id,
                "title": info.get('title'),
                "duration": info.get('duration'),
                "file_path": output_file,
            }

        except HTTPException as he:
            # すでにHTTPExceptionの場合はそのまま再送出
            raise he
        except Exception as e:
            logger.error(f"Error during audio extraction: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

        
        
    async def _get_video_info(self, url: str) -> Dict:
        """動画の情報を取得"""
        try:
            # URLの形式を検証
            if not self._is_valid_youtube_url(url):
                raise HTTPException(status_code=400, detail="Invalid YouTube URL format")

            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                try:
                    info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                    if not info:
                        raise HTTPException(status_code=400, detail="Video not found")
                    return info
                except yt_dlp.utils.DownloadError as e:
                    raise HTTPException(status_code=400, detail=str(e))
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            raise HTTPException(status_code=400, detail="Could not get video information")

    def _is_valid_youtube_url(self, url: str) -> bool:
        """YouTubeのURL形式を検証"""
        # 簡単な正規表現を使用してURLの形式を検証
        import re
        pattern = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}$'
        return re.match(pattern, url) is not None




    async def _download_and_convert(self, url: str, video_id: str) -> str:
        """動画をダウンロードしMP3に変換"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                await asyncio.to_thread(ydl.download, [url])
                
            output_file = f"{self.temp_dir}/{video_id}.mp3"
            
            if not os.path.exists(output_file):
                raise HTTPException(status_code=400, detail="File conversion failed")
                
            return output_file

        except Exception as e:
            logger.error(f"Error downloading/converting: {str(e)}")
            raise HTTPException(status_code=400, detail="Download or conversion failed")