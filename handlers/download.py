import logging
import os
import re
import uuid

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import Config
from services.downloader import DownloadError, download_media, extract_info

router = Router()
logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"(https?://\S+)")

# Telegram URL orqali yuboriladigan faylga ~20MB limit.
URL_SEND_LIMIT_MB = 20

# Havolalarni vaqtincha saqlaymiz (callback_data 64 bayt bilan cheklangan).
pending_links: dict[str, str] = {}

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
async def handle_link(message: Message) -> None:
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

    link_id = uuid.uuid4().hex[:8]
    pending_links[link_id] = url

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡️ Video (tez)", callback_data=f"dl:fast:{link_id}"
                ),
                InlineKeyboardButton(
                    text="💎 Video (sifatli)", callback_data=f"dl:best:{link_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎵 Audio (mp3)", callback_data=f"dl:audio:{link_id}"
                ),
            ],
        ]
    )

    await message.answer(
        f"✅ {PLATFORM_NAMES[platform]} havolasi qabul qilindi.\n"
        "Qaysi formatda yuklab olay?",
        reply_markup=keyboard,
    )


async def _send_via_url(message: Message, url: str, status: Message) -> bool:
    """'fast' rejim: to'g'ridan-to'g'ri URL yuborishga urinadi.

    Muvaffaqiyatli bo'lsa True qaytaradi.
    """
    try:
        info = await extract_info(url)
    except Exception:  # noqa: BLE001
        logger.exception("extract_info xatosi")
        return False

    direct_url = info["direct_url"]
    filesize_mb = (info["filesize"] / (1024 * 1024)) if info["filesize"] else None
    caption = info["title"][:1000] if info["title"] else None
    small_enough = (filesize_mb is None) or (filesize_mb <= URL_SEND_LIMIT_MB)

    if direct_url and not info["needs_merge"] and small_enough:
        try:
            await message.answer_video(direct_url, caption=caption)
            await status.delete()
            return True
        except TelegramBadRequest as exc:
            logger.info("URL bilan yuborib bo'lmadi: %s", exc)
    return False


async def _download_and_send(
    message: Message, url: str, fmt: str, status: Message, config: Config
) -> None:
    """Serverga yuklab olib, fayl sifatida yuboradi."""
    await status.edit_text("⏳ Yuklab olinmoqda...")
    try:
        file_path, title = await download_media(url, fmt, config.download_dir)
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
                f"({config.max_file_size_mb}MB) dan katta. "
                "⚡️ Video (tez) variantni sinab ko'ring."
            )
            return
        caption = title[:1000] if title else None
        if fmt == "audio":
            await message.answer_audio(FSInputFile(file_path), caption=caption)
        else:
            await message.answer_video(FSInputFile(file_path), caption=caption)
        await status.delete()
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.callback_query(F.data.startswith("dl:"))
async def handle_choice(callback: CallbackQuery, config: Config) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return

    _, fmt, link_id = callback.data.split(":")
    url = pending_links.get(link_id)
    if not url:
        await callback.message.edit_text(
            "❌ Havola muddati tugagan. Iltimos, qaytadan yuboring."
        )
        return

    status = await callback.message.edit_text("⏳ Tayyorlanmoqda...")

    # "fast" rejimda avval to'g'ridan-to'g'ri URL yuborishga urinamiz
    if fmt == "fast":
        if await _send_via_url(callback.message, url, status):
            pending_links.pop(link_id, None)
            return
        # bo'lmasa — yuklab olishga o'tamiz

    await _download_and_send(callback.message, url, fmt, status, config)
    pending_links.pop(link_id, None)
