import yt_dlp
import os
import asyncio
import logging
from typing import Dict
from fastapi import HTTPException
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import requests

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
            'writethumbnail': True,  # サムネイル取得を有効化
            'outtmpl': f'{self.temp_dir}/%(title)s.%(ext)s',  # タイトルベースのファイル名
            'quiet': True,
            'no_warnings': True,
        }

    async def _set_media_tags(self, file_path: str, info: Dict) -> None:
        """メディアタグを設定"""
        try:
            try:
                audio = EasyID3(file_path)
            except:
                audio = ID3()
                audio.save(file_path)
                audio = EasyID3(file_path)

            # 基本的なタグを設定
            audio['title'] = info.get('title', '')
            audio['artist'] = info.get('uploader', '')
            audio['album'] = 'YouTube Music'
            if info.get('upload_date'):
                audio['date'] = f"{info['upload_date'][:4]}"  # 年のみ使用
            audio.save()

            # サムネイル画像を設定
            if info.get('thumbnail'):
                try:
                    audio = ID3(file_path)
                    response = requests.get(info['thumbnail'])
                    if response.status_code == 200:
                        audio.add(APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,
                            desc='Cover',
                            data=response.content
                        ))
                        audio.save()
                except Exception as e:
                    logger.error(f"Error setting thumbnail: {str(e)}")

        except Exception as e:
            logger.error(f"Error setting media tags: {str(e)}")
            # タグ設定の失敗は致命的ではないのでエラーは投げない

    async def extract(self, url: str) -> Dict:
        """音声を抽出してタグを設定"""
        try:
            # 動画情報を取得
            info = await self._get_video_info(url)
            if not info:
                raise HTTPException(status_code=400, detail="Could not get video information")

            # ファイル名から使用できない文字を除去
            safe_title = "".join(c for c in info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_path = f"{self.temp_dir}/{safe_title}"
            self.ydl_opts['outtmpl'] = output_path + '.%(ext)s'

            # 音声をダウンロード
            output_file = await self._download_and_convert(url, info['id'])
            
            # メディアタグを設定
            await self._set_media_tags(output_file, info)

            return {
                "video_id": info['id'],
                "title": info['title'],
                "duration": info.get('duration'),
                "file_path": output_file,
                "filename": f"{safe_title}.mp3"
            }

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
            
    async def _download_and_convert(self, url: str, video_id: str) -> str:
        """動画をダウンロードしMP3に変換"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                await asyncio.to_thread(ydl.download, [url])
                
            # 出力ファイルのパスを構築（ファイル名はextractメソッドで設定済み）
            output_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.mp3')]
            if not output_files:
                raise HTTPException(status_code=400, detail="File conversion failed")
                    
            return os.path.join(self.temp_dir, output_files[0])

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error downloading/converting: {str(e)}")
            raise HTTPException(status_code=400, detail="Download or conversion failed")

    async def _get_video_info(self, url: str) -> Dict:
        """動画の情報を取得"""
        try:
            # URLの厳密なバリデーション
            if not self._is_valid_youtube_url(url):
                raise HTTPException(status_code=400, detail="Invalid YouTube URL format")

            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                try:
                    info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                    if not info or 'id' not in info:
                        raise HTTPException(status_code=400, detail="Video not found or not accessible")
                    return info
                except yt_dlp.utils.ExtractorError as e:
                    raise HTTPException(status_code=400, detail=f"Could not extract video info: {str(e)}")
                except yt_dlp.utils.DownloadError as e:
                    raise HTTPException(status_code=400, detail=f"Video not available: {str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            raise HTTPException(status_code=400, detail="Could not process video URL")

    def _is_valid_youtube_url(self, url: str) -> bool:
        """YouTubeのURLが有効かチェック"""
        import re
        youtube_regex = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]{11}$'
        return bool(re.match(youtube_regex, url))