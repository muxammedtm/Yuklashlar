import asyncio
import os
import uuid

import yt_dlp

from services import ffmpeg_setup


class DownloadError(Exception):
    """yt-dlp xatolikka uchraganda chiqariladi."""


# Format tanlovlari:
#   "fast"  -> bitta tayyor progressiv fayl (merge yo'q, tez, lekin xira)
#   "best"  -> eng yaxshi video+audio (kerak bo'lsa merge qilinadi, sifatli)
#   "audio" -> faqat audio (mp3)
FORMAT_MAP = {
    "fast": (
        "best[ext=mp4][acodec!=none][vcodec!=none]/"
        "best[acodec!=none][vcodec!=none]/best"
    ),
    # 720p gacha cheklangan — sifatli, lekin hajm odatda 50MB ichida
    "best": (
        "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/"
        "best[height<=720][ext=mp4]/"
        "best[height<=720]/best"
    ),
    "audio": "bestaudio/best",
}


# --- TEZ USUL: faqat to'g'ridan-to'g'ri havola olish (yuklab olmasdan) ---

def _extract_sync(url: str) -> dict:
    """Videoni YUKLAMASDAN ma'lumotini oladi (faqat 'fast' rejim uchun)."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": FORMAT_MAP["fast"],
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(str(exc)) from exc

    direct_url = info.get("url")
    if not direct_url:
        formats = info.get("requested_formats") or []
        if len(formats) == 1:
            direct_url = formats[0].get("url")

    return {
        "direct_url": direct_url,
        "title": info.get("title") or "",
        "filesize": info.get("filesize") or info.get("filesize_approx"),
        "ext": info.get("ext") or "mp4",
        "needs_merge": bool(
            info.get("requested_formats") and len(info["requested_formats"]) > 1
        ),
    }


async def extract_info(url: str) -> dict:
    return await asyncio.to_thread(_extract_sync, url)


# --- YUKLAB OLISH USULI ---

def _build_opts(fmt: str, output_template: str) -> dict:
    base_opts = {
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "format": FORMAT_MAP.get(fmt, FORMAT_MAP["fast"]),
        # "cookiefile": "data/instagram_cookies.txt",
    }

    if ffmpeg_setup.FFMPEG_DIR:
        base_opts["ffmpeg_location"] = ffmpeg_setup.FFMPEG_DIR

    if fmt == "best":
        base_opts["merge_output_format"] = "mp4"

    if fmt == "audio":
        base_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    return base_opts


def _download_sync(url: str, fmt: str, download_dir: str) -> tuple[str, str]:
    file_id = uuid.uuid4().hex
    output_template = os.path.join(download_dir, f"{file_id}.%(ext)s")
    opts = _build_opts(fmt, output_template)

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_path = ydl.prepare_filename(info)
            if fmt == "audio":
                final_path = os.path.splitext(final_path)[0] + ".mp3"
            elif fmt == "best":
                # merge natijasi .mp4 bo'ladi
                base = os.path.splitext(final_path)[0]
                if os.path.exists(base + ".mp4"):
                    final_path = base + ".mp4"
            return final_path, info.get("title") or ""
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(str(exc)) from exc


async def download_media(url: str, fmt: str, download_dir: str) -> tuple[str, str]:
    return await asyncio.to_thread(_download_sync, url, fmt, download_dir)
