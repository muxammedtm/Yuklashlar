import logging
import os
import re

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile, Message

from config import Config
from services.downloader import DownloadError, download_media, extract_info

router = Router()
logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"(https?://\S+)")

# Telegram URL orqali yuboriladigan faylga ~20MB limit qo'yadi.
# Shundan kichik bo'lsa — URL yuboramiz (tez). Kattaroq bo'lsa yoki
# hajm noma'lum bo'lsa — o'zimiz yuklab beramiz.
URL_SEND_LIMIT_MB = 20

PLATFORM_NAMES = {
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "youtube": "YouTube",
}


def detect_platform(url: str) -> str | None:
    url = url.lower()
    if "instagram.com" in url:
        return "instagram"
    if "tiktok.com" in url:
        return "tiktok"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return None


@router.message(F.text.regexp(URL_PATTERN))
async def handle_link(message: Message, config: Config) -> None:
    match = URL_PATTERN.search(message.text or "")
    if not match:
        return

    url = match.group(1)
    platform = detect_platform(url)

    if platform is None:
        await message.answer(
            "❗️ Bu havola hozircha qo'llab-quvvatlanmaydi.\n"
            "Faqat Instagram, TikTok va YouTube havolalarini qabul qilaman."
        )
        return

    status = await message.answer("⏳ Tayyorlanmoqda...")

    # 1) TEZ USUL: to'g'ridan-to'g'ri havolani olishga urinamiz
    try:
        info = await extract_info(url)
    except DownloadError as exc:
        await status.edit_text(f"❌ Xatolik: {exc}")
        return
    except Exception:  # noqa: BLE001
        logger.exception("extract_info xatosi")
        await status.edit_text("❌ Ma'lumot olishda xatolik yuz berdi.")
        return

    direct_url = info["direct_url"]
    filesize_mb = (info["filesize"] / (1024 * 1024)) if info["filesize"] else None
    caption = info["title"][:1000] if info["title"] else None

    small_enough = (filesize_mb is None) or (filesize_mb <= URL_SEND_LIMIT_MB)

    if direct_url and not info["needs_merge"] and small_enough:
        # Telegram'ga to'g'ridan-to'g'ri URL beramiz — Telegram o'zi tortadi
        try:
            await message.answer_video(direct_url, caption=caption)
            await status.delete()
            return
        except TelegramBadRequest as exc:
            logger.info("URL bilan yuborib bo'lmadi, yuklab olamiz: %s", exc)

    # 2) ZAXIRA USUL: serverga yuklab olib, fayl sifatida yuboramiz
    await status.edit_text("⏳ Yuklab olinmoqda...")
    try:
        file_path, dl_title = await download_media(url, "video", config.download_dir)
    except DownloadError as exc:
        await status.edit_text(f"❌ Xatolik: {exc}")
        return
    except Exception:  # noqa: BLE001
        logger.exception("download_media xatosi")
        await status.edit_text("❌ Yuklab olishda xatolik yuz berdi.")
        return

    try:
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > config.max_file_size_mb:
            await status.edit_text(
                f"❌ Fayl hajmi {size_mb:.1f}MB — Telegram limiti "
                f"({config.max_file_size_mb}MB) dan katta."
            )
            return
        await message.answer_video(
            FSInputFile(file_path),
            caption=(dl_title[:1000] if dl_title else None),
        )
        await status.delete()
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
