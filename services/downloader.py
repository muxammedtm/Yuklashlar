import asyncio
import os
import uuid

import yt_dlp

from services import ffmpeg_setup


class DownloadError(Exception):
    """yt-dlp xatolikka uchraganda chiqariladi."""


# --- TEZ USUL: faqat to'g'ridan-to'g'ri havola olish (yuklab olmasdan) ---

def _extract_sync(url: str) -> dict:
    """Videoni YUKLAMASDAN, faqat ma'lumotini oladi.

    Qaytaradi: {"direct_url", "title", "filesize", "ext", "is_progressive"}
    """
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        # Audio+video bitta faylda bo'lgan (merge talab qilmaydigan)
        # progressiv formatni afzal ko'ramiz — Instagram aynan shunaqa beradi.
        "format": (
            "best[ext=mp4][acodec!=none][vcodec!=none]/"
            "best[acodec!=none][vcodec!=none]/best"
        ),
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(str(exc)) from exc

    # Tanlangan formatning to'g'ridan-to'g'ri havolasi
    direct_url = info.get("url")
    # Ba'zan url tepa darajada bo'lmaydi — formats ichidan olamiz
    if not direct_url:
        formats = info.get("requested_formats") or []
        if len(formats) == 1:
            direct_url = formats[0].get("url")

    filesize = info.get("filesize") or info.get("filesize_approx")

    return {
        "direct_url": direct_url,
        "title": info.get("title") or "",
        "filesize": filesize,  # baytlarda yoki None
        "ext": info.get("ext") or "mp4",
        # merge kerakmi? (requested_formats >1 bo'lsa — kerak)
        "needs_merge": bool(info.get("requested_formats")
                            and len(info["requested_formats"]) > 1),
    }


async def extract_info(url: str) -> dict:
    """Videoni yuklamasdan ma'lumotini oladi (tez usul uchun)."""
    return await asyncio.to_thread(_extract_sync, url)


# --- ZAXIRA USUL: faylni serverga yuklab olish (URL ishlamaganda) ---

def _build_opts(fmt: str, output_template: str) -> dict:
    base_opts = {
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # "cookiefile": "data/instagram_cookies.txt",
    }

    if ffmpeg_setup.FFMPEG_DIR:
        base_opts["ffmpeg_location"] = ffmpeg_setup.FFMPEG_DIR

    if fmt == "audio":
        base_opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        )
    else:
        # Bitta progressiv fayl (merge yo'q) — kichik va tez
        base_opts["format"] = (
            "best[ext=mp4][acodec!=none][vcodec!=none]/"
            "best[acodec!=none][vcodec!=none]/best"
        )

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
            return final_path, info.get("title") or ""
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(str(exc)) from exc


async def download_media(url: str, fmt: str, download_dir: str) -> tuple[str, str]:
    """Video/audio'ni serverga yuklab oladi (zaxira usul)."""
    return await asyncio.to_thread(_download_sync, url, fmt, download_dir)
