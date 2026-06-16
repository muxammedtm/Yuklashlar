import asyncio
import os
import uuid

import yt_dlp

from services import ffmpeg_setup


class DownloadError(Exception):
    """yt-dlp video/audio yuklab olishda xatolikka uchraganda chiqariladi."""


def _build_opts(fmt: str, output_template: str) -> dict:
    base_opts = {
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # Instagram'ning ba'zi (private/login talab qiladigan) postlari uchun
        # tarmoqdan eksport qilingan cookies fayl kerak bo'lishi mumkin:
        # "cookiefile": "data/instagram_cookies.txt",
    }

    # ffmpeg papkasini to'g'ridan-to'g'ri yt-dlp'ga beramiz
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
        base_opts.update(
            {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
            }
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
                # FFmpegExtractAudio fayl kengaytmasini .mp3 ga o'zgartiradi
                final_path = os.path.splitext(final_path)[0] + ".mp3"

            title = info.get("title") or ""
            return final_path, title
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(str(exc)) from exc


async def download_media(url: str, fmt: str, download_dir: str) -> tuple[str, str]:
    """Video/audio'ni asinxron tarzda yuklab oladi (alohida threadda).

    Qaytaradi: (fayl_yo'li, video_sarlavhasi)
    """
    return await asyncio.to_thread(_download_sync, url, fmt, download_dir)
