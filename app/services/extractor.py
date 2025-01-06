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
            'extract_flat': True,  # プレイリスト情報を取得
            'noplaylist': False    # プレイリスト情報を許可
        }

    

    async def _get_video_info(self, url: str) -> Dict:
        """動画の情報を取得"""
        try:
            # まず正しい動画IDを取得
            video_id = self._extract_video_id(url)
            logger.info(f"Extracted video ID from URL: {video_id}")

            # プレイリスト情報用の設定
            playlist_opts = {
                **self.ydl_opts,
                'extract_flat': True,
                'noplaylist': False,
            }

            # 単一動画情報用の設定
            video_opts = {
                **self.ydl_opts,
                'extract_flat': False,
                'noplaylist': True,
            }

            with yt_dlp.YoutubeDL(playlist_opts) as ydl:
                try:
                    # プレイリスト情報の取得を試みる
                    playlist_info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                    
                    # プレイリスト情報の保存
                    playlist_data = None
                    if playlist_info.get('_type') == 'playlist':
                        playlist_data = {
                            'playlist_title': playlist_info.get('title'),
                            'playlist_id': playlist_info.get('id'),
                        }
                        logger.info(f"Found playlist info: {playlist_data}")

                    # 単一動画の情報を取得
                    with yt_dlp.YoutubeDL(video_opts) as video_ydl:
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        video_info = await asyncio.to_thread(video_ydl.extract_info, video_url, download=False)

                        if not video_info or 'id' not in video_info:
                            raise HTTPException(status_code=400, detail="Video not found")

                        # プレイリスト情報があれば追加
                        if playlist_data:
                            video_info.update(playlist_data)

                        logger.info(f"Successfully retrieved video info - Title: {video_info.get('title')}, ID: {video_info.get('id')}")
                        return video_info

                except yt_dlp.utils.ExtractorError as e:
                    logger.error(f"Extractor error: {str(e)}")
                    raise HTTPException(status_code=400, detail=f"Could not extract video info: {str(e)}")
                except yt_dlp.utils.DownloadError as e:
                    logger.error(f"Download error: {str(e)}")
                    raise HTTPException(status_code=400, detail=f"Video not available: {str(e)}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=400, detail="Could not process video URL")

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
            # メタデータの設定
            try:
                audio = EasyID3(file_path)
            except error:
                audio = ID3()
                audio.save(file_path)
                audio = EasyID3(file_path)

            # 基本的なメタデータを設定
            title = info.get('title', '')
            artist = info.get('uploader', '')
            album = info.get('playlist_title', '') or info.get('album', 'YouTube Music')

            audio['title'] = title
            audio['artist'] = artist
            audio['album'] = album
            if info.get('upload_date'):
                audio['date'] = info['upload_date'][:4]
            audio.save()

            # 画像の設定
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
                    logger.info(f"Set metadata - Title: {title}, Artist: {artist}, Album: {album}")

        except Exception as e:
            logger.error(f"Error setting media tags: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            
            
    async def _download_and_convert(self, url: str, video_id: str) -> str:
        """動画をダウンロードしMP3に変換"""
        try:
            # プレイリストの場合でも動画を直接ダウンロードするための設定
            download_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'writethumbnail': True,
                'outtmpl': f'{self.temp_dir}/%(id)s.%(ext)s',
                'quiet': False,  # デバッグのために出力を有効化
                'no_warnings': False,  # 警告も表示
                'noplaylist': True,  # プレイリストを無視
            }

            logger.info(f"Starting download for video ID: {video_id}")
            logger.info(f"Original URL: {url}")
            
            # 直接動画URLを構築
            single_video_url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"Using direct video URL: {single_video_url}")

            try:
                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    # ダウンロード前の情報を取得
                    info = await asyncio.to_thread(ydl.extract_info, single_video_url, download=False)
                    logger.info(f"Pre-download info: {info.get('title') if info else 'No info'}")
                    
                    # ダウンロードを実行
                    await asyncio.to_thread(ydl.download, [single_video_url])
                    logger.info("Download completed successfully")

            except Exception as e:
                logger.error(f"Download error: {str(e)}")
                raise

            # ファイル確認
            all_files = os.listdir(self.temp_dir)
            logger.info(f"All files in temp directory: {all_files}")
            
            mp3_files = [f for f in all_files if f.endswith('.mp3')]
            logger.info(f"Found MP3 files: {mp3_files}")

            if not mp3_files:
                logger.error("No MP3 files found after conversion")
                raise HTTPException(status_code=400, detail="File conversion failed")

            target_mp3 = f"{video_id}.mp3"
            if target_mp3 in mp3_files:
                output_path = os.path.join(self.temp_dir, target_mp3)
            else:
                output_path = os.path.join(self.temp_dir, mp3_files[0])
                
            logger.info(f"Final output path: {output_path}")
            
            if not os.path.exists(output_path):
                logger.error(f"Output file does not exist: {output_path}")
                raise HTTPException(status_code=400, detail="File not found after conversion")

            return output_path

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error in download_and_convert: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=400, detail="Download or conversion failed")


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
    
        
        
    """プレイリスト機能"""
    async def is_playlist(self, url: str) -> bool:
        """URLがプレイリストかどうかを判定"""
        try:
            info = await self.get_playlist_info(url)
            return info.get('_type') == 'playlist'
        except Exception as e:
            logger.error(f"Error checking if URL is playlist: {str(e)}")
            return False

    async def get_playlist_info(self, url: str) -> Dict:
        """プレイリストの情報を取得"""
        playlist_opts = {
            **self.ydl_opts,
            'extract_flat': True,
            'noplaylist': False,
            'quiet': False,  # デバッグのために出力を有効化
        }

        try:
            with yt_dlp.YoutubeDL(playlist_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                logger.info(f"Retrieved info type: {info.get('_type')}")
                logger.info(f"Retrieved info keys: {info.keys()}")

                # プレイリスト情報の構造を確認
                if info.get('_type') != 'playlist':
                    # プレイリストでない場合は単一の動画として扱う
                    return {
                        'title': 'Single Video Playlist',
                        '_type': 'playlist',
                        'entries': [{
                            'id': info.get('id'),
                            'title': info.get('title'),
                            'url': url
                        }]
                    }

                if 'entries' not in info:
                    raise HTTPException(
                        status_code=400, 
                        detail="Could not retrieve playlist entries"
                    )

                # エントリーの数をログ
                logger.info(f"Found {len(info.get('entries', []))} videos in playlist")
                return info

        except Exception as e:
            logger.error(f"Error getting playlist info: {str(e)}")
            raise HTTPException(
                status_code=400, 
                detail=f"Could not get playlist info: {str(e)}"
            )