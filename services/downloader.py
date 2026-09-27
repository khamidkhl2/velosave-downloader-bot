import os
import shutil
import tempfile
import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional
import aiohttp
import yt_dlp

from config import config

logger = logging.getLogger(__name__)

class FileSizeExceededError(Exception):
    def __init__(self, size_bytes: int):
        self.size_bytes = size_bytes
        self.size_mb = size_bytes / (1024 * 1024)
        super().__init__(f"File size {self.size_mb:.1f} MB exceeds limit")

class MediaDownloadError(Exception):
    pass

@dataclass
class DownloadedItem:
    file_path: str
    media_type: str  # 'video', 'photo', 'audio'
    title: str = ""
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: int = 0

@dataclass
class DownloadResult:
    items: List[DownloadedItem]
    temp_dir: str
    title: str = ""

    def cleanup(self):
        """Removes the temporary directory and all files inside."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Error removing temp dir {self.temp_dir}: {e}")

class DownloaderService:
    def __init__(self):
        self.max_size = config.MAX_FILESIZE_BYTES
        self.temp_base = config.TEMP_DIR

    async def download(self, url: str) -> DownloadResult:
        """
        Downloads media from supported social media platforms:
        Instagram, TikTok, YouTube, Pinterest, etc.
        """
        temp_dir = tempfile.mkdtemp(dir=self.temp_base, prefix="saveflow_")
        try:
            # Check if this is a direct image URL (e.g. Pinterest direct image or image CDN)
            if self._is_direct_image_url(url):
                item = await self._download_direct_image(url, temp_dir)
                return DownloadResult(items=[item], temp_dir=temp_dir, title=item.title)

            # Otherwise use yt-dlp for video/photo posts
            result = await asyncio.to_thread(self._yt_dlp_download, url, temp_dir)
            return result
        except Exception:
            # Clean up on failure before re-raising
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    def _is_direct_image_url(self, url: str) -> bool:
        clean_url = url.split("?")[0].lower()
        return clean_url.endswith((".jpg", ".jpeg", ".png", ".webp")) or "i.pinimg.com/" in url

    async def _download_direct_image(self, url: str, temp_dir: str) -> DownloadedItem:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        dest_path = os.path.join(temp_dir, "image.jpg")
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    raise MediaDownloadError(f"HTTP error {resp.status} downloading image")
                
                content_length = resp.headers.get("Content-Length")
                if content_length and int(content_length) > self.max_size:
                    raise FileSizeExceededError(int(content_length))

                content = await resp.read()
                if len(content) > self.max_size:
                    raise FileSizeExceededError(len(content))

                with open(dest_path, "wb") as f:
                    f.write(content)

        return DownloadedItem(
            file_path=dest_path,
            media_type="photo",
            title="Pinterest Image",
            size_bytes=os.path.getsize(dest_path)
        )

    def _yt_dlp_download(self, url: str, temp_dir: str) -> DownloadResult:
        outtmpl = os.path.join(temp_dir, "%(id)s.%(ext)s")
        ydl_opts = {
            "outtmpl": outtmpl,
            "format": f"bestvideo[height<={config.MAX_VIDEO_HEIGHT}][ext=mp4]+bestaudio[ext=m4a]/best[height<={config.MAX_VIDEO_HEIGHT}][ext=mp4]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "max_filesize": self.max_size,
            "socket_timeout": 30,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise MediaDownloadError("No media found at URL")
        except yt_dlp.utils.MaxDownloadsReached:
            raise
        except yt_dlp.utils.DownloadError as e:
            err_str = str(e).lower()
            if "file is larger than max-filesize" in err_str or "exceeds maximum file size" in err_str:
                raise FileSizeExceededError(self.max_size)
            raise MediaDownloadError(f"yt-dlp download failed: {e}")
        except Exception as e:
            raise MediaDownloadError(f"Extraction error: {e}")

        # Scan the directory for downloaded media files
        items: List[DownloadedItem] = []
        video_exts = {".mp4", ".mov", ".mkv", ".webm"}
        image_exts = {".jpg", ".jpeg", ".png", ".webp"}
        audio_exts = {".mp3", ".m4a", ".aac", ".ogg", ".opus"}

        entries = os.listdir(temp_dir)
        if not entries:
            raise MediaDownloadError("No files downloaded")

        title = info.get("title", "") or info.get("description", "") or "Media"
        if len(title) > 60:
            title = title[:57] + "..."

        for filename in entries:
            ext = os.path.splitext(filename)[1].lower()
            file_path = os.path.join(temp_dir, filename)
            
            # Skip hidden files or part files
            if filename.startswith(".") or ext in {".part", ".ytdl"}:
                continue

            file_size = os.path.getsize(file_path)
            if file_size > self.max_size:
                raise FileSizeExceededError(file_size)

            if ext in video_exts:
                items.append(DownloadedItem(
                    file_path=file_path,
                    media_type="video",
                    title=title,
                    duration=info.get("duration"),
                    width=info.get("width"),
                    height=info.get("height"),
                    size_bytes=file_size
                ))
            elif ext in image_exts:
                items.append(DownloadedItem(
                    file_path=file_path,
                    media_type="photo",
                    title=title,
                    size_bytes=file_size
                ))
            elif ext in audio_exts:
                items.append(DownloadedItem(
                    file_path=file_path,
                    media_type="audio",
                    title=title,
                    duration=info.get("duration"),
                    size_bytes=file_size
                ))

        if not items:
            raise MediaDownloadError("No valid media files produced")

        return DownloadResult(items=items, temp_dir=temp_dir, title=title)

downloader_service = DownloaderService()
