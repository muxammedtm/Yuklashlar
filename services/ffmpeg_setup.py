import logging
import os

logger = logging.getLogger(__name__)

# ffmpeg va ffprobe binarlari joylashgan papka. yt-dlp'ga shu papkani
# to'g'ridan-to'g'ri "ffmpeg_location" sifatida beramiz — bu PATH'ga
# tayanishdan ko'ra ancha ishonchli.
FFMPEG_DIR: str | None = None


def setup_ffmpeg() -> str | None:
    """static-ffmpeg orqali ffmpeg/ffprobe ni tayyorlaydi.

    Binarlar joylashgan papka yo'lini qaytaradi (yoki topilmasa None).
    """
    global FFMPEG_DIR

    try:
        from static_ffmpeg import run

        ffmpeg_path, ffprobe_path = (
            run.get_or_fetch_platform_executables_else_raise()
        )
        FFMPEG_DIR = os.path.dirname(ffmpeg_path)
        logger.info("ffmpeg tayyor: %s", ffmpeg_path)
        logger.info("ffprobe tayyor: %s", ffprobe_path)
        return FFMPEG_DIR
    except Exception:  # noqa: BLE001
        logger.exception("static-ffmpeg ni tayyorlashda xatolik")
        return None
