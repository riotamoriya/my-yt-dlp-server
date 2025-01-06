import yt_dlp
import os
import asyncio
import logging
from typing import Dict
from fastapi import HTTPException
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, error
import requests
from PIL import Image
import io

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
            'writethumbnail': True,
            'outtmpl': f'{self.temp_dir}/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,  # この設定を追加
            'extract_flat': False  # この設定も追加
        }

    def center_crop_square(self, img: Image.Image) -> Image.Image:
        """画像を中央から正方形にクロップ"""
        width, height = img.size
        if width == height:
            return img
        
        new_size = min(width, height)
        # 中央を基準にクロップする位置を計算
        left = (width - new_size) // 2
        top = (height - new_size) // 2
        right = left + new_size
        bottom = top + new_size
        
        # クロップを実行
        logger.info(f"Cropping image from {width}x{height} to {new_size}x{new_size}")
        return img.crop((left, top, right, bottom))
        
        
    async def cleanup_old_files(self, keep_latest: int = 5):
        """最新のN個以外の一時ファイルを削除"""
        try:
            files = []
            for f in os.listdir(self.temp_dir):
                path = os.path.join(self.temp_dir, f)
                if os.path.isfile(path):
                    files.append((path, os.path.getmtime(path)))
            
            # 更新時刻で並べ替え
            files.sort(key=lambda x: x[1], reverse=True)
            
            # 古いファイルを削除
            for file_path, _ in files[keep_latest:]:
                try:
                    os.remove(file_path)
                    logger.info(f"Cleaned up old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting file {file_path}: {e}")
                    
            return len(files[keep_latest:])  # 削除したファイル数を返す
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
    
    async def extract(self, url: str) -> Dict:
            """音声を抽出してタグを設定"""
            try:
                info = await self._get_video_info(url)
                if not info:
                    raise HTTPException(status_code=400, detail="Could not get video information")

                output_file = await self._download_and_convert(url, info['id'])
                await self._set_media_tags(output_file, info)

                safe_title = "".join(c for c in info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                
                result = {
                    "video_id": info['id'],
                    "title": info['title'],
                    "duration": info.get('duration'),
                    "file_path": output_file,
                    "filename": f"{safe_title}.mp3"
                }
                cleaned = await self.cleanup_old_files(keep_latest=5)
                
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} old files")
                    
                return result
                

            except HTTPException as he:
                raise he
            except Exception as e:
                logger.error(f"Error during extraction: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
    
    

    async def _set_media_tags(self, file_path: str, info: Dict) -> None:
        """メディアタグを設定"""
        try:
            thumbnails = [
                info.get('thumbnail'),
                next((t['url'] for t in info.get('thumbnails', []) if t.get('url')), None),
                f"https://i.ytimg.com/vi/{info['id']}/maxresdefault.jpg",
                f"https://i.ytimg.com/vi/{info['id']}/hqdefault.jpg"
            ]
            
            thumbnail_url = next((url for url in thumbnails if url), None)
            logger.info(f"Selected thumbnail URL: {thumbnail_url}")

            if thumbnail_url:
                response = requests.get(thumbnail_url)
                if response.status_code == 200:
                    # 画像をPILで開く
                    img = Image.open(io.BytesIO(response.content))
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # 画像を正方形にクロップ
                    img = self.center_crop_square(img)
                    
                    # JPEG形式で保存
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=95)
                    image_data = output.getvalue()
                    
                    # ID3タグに画像を追加
                    audio = ID3(file_path)
                    audio.delall('APIC')  # 既存の画像を削除
                    
                    audio.add(APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Cover',
                        data=image_data
                    ))
                    audio.save(v2_version=3)
                    
                    # 検証
                    verify_audio = ID3(file_path)
                    apic_frames = verify_audio.getall('APIC')
                    logger.info(f"Embedded image size: {len(image_data)} bytes")
                    logger.info(f"Number of APIC frames: {len(apic_frames)}")

        except Exception as e:
            logger.error(f"Error setting media tags: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
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
            if not self._is_valid_youtube_url(url):
                raise HTTPException(status_code=400, detail="Invalid YouTube URL format")

            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                try:
                    # URLの内容をログ出力
                    logger.info(f"Processing URL: {url}")
                    
                    info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                    
                    # 取得した情報の内容をログ出力
                    logger.info(f"Retrieved info type: {type(info)}")
                    logger.info(f"Retrieved info keys: {info.keys() if info else 'None'}")
                    
                    if not info or 'id' not in info:
                        raise HTTPException(status_code=400, detail="Video not found or not accessible")
                    
                    # 最終的に使用する情報をログ出力
                    logger.info(f"Using video ID: {info['id']}")
                    logger.info(f"Using title: {info.get('title')}")
                    
                    return info

                except yt_dlp.utils.ExtractorError as e:
                    logger.error(f"Extractor error: {str(e)}")
                    raise HTTPException(status_code=400, detail=f"Could not extract video info: {str(e)}")
                except yt_dlp.utils.DownloadError as e:
                    logger.error(f"Download error: {str(e)}")
                    raise HTTPException(status_code=400, detail=f"Video not available: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            raise HTTPException(status_code=400, detail="Could not process video URL")


    def _extract_video_id(self, url: str) -> str:
        """URLから動画IDを抽出"""
        import re
        import urllib.parse

        # URLをパース
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # 'v' パラメータから動画IDを取得
        video_id = query_params.get('v', [None])[0]
        
        if not video_id:
            # youtu.be形式の場合
            if 'youtu.be' in url:
                video_id = parsed_url.path.strip('/')
        
        if not video_id or len(video_id) != 11:
            logger.error(f"Invalid video ID extracted from URL: {url}")
            raise HTTPException(status_code=400, detail="Could not extract valid video ID")
        
        logger.info(f"Extracted video ID: {video_id}")
        return video_id


    def _is_valid_youtube_url(self, url: str) -> bool:
        """YouTubeのURLが有効かチェック"""
        import re
        # URLからビデオIDを直接抽出
        video_id_pattern = r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
        video_id_match = re.search(video_id_pattern, url)
        
        return bool(video_id_match)