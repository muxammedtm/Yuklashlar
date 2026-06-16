import logging
import os
import re
import uuid

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import Config
from services.downloader import DownloadError, download_media

router = Router()
logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"(https?://\S+)")

# Havolalarni vaqtincha xotirada saqlaymiz, chunki Telegram callback_data
# uzunligi 64 bayt bilan cheklangan va to'liq URL sig'masligi mumkin.
# Eslatma: bot qayta ishga tushganda (deploy/restart) bu lug'at tozalanadi —
# katta yuklamada Redis/bazaga o'tkazish tavsiya etiladi.
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
            "Hozircha faqat Instagram, TikTok va YouTube havolalarini qabul qilaman."
        )
        return

    link_id = uuid.uuid4().hex[:8]
    pending_links[link_id] = url

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎥 Video", callback_data=f"dl:video:{link_id}"),
                InlineKeyboardButton(text="🎵 Audio (mp3)", callback_data=f"dl:audio:{link_id}"),
            ]
        ]
    )

    await message.answer(
        f"✅ {PLATFORM_NAMES[platform]} havolasi qabul qilindi.\n"
        "Qaysi formatda yuklab olay?",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("dl:"))
async def handle_download_choice(callback: CallbackQuery, config: Config) -> None:
    await callback.answer()  # tugma ustidagi "loading" holatini to'xtatish

    if not callback.data or not callback.message:
        return

    _, fmt, link_id = callback.data.split(":")
    url = pending_links.get(link_id)

    if not url:
        await callback.message.edit_text("❌ Havola muddati tugagan. Iltimos, qaytadan yuboring.")
        return

    status_msg = await callback.message.edit_text("⏳ Yuklab olinmoqda, biroz kuting...")

    try:
        file_path, title = await download_media(url, fmt, config.download_dir)
    except DownloadError as exc:
        await status_msg.edit_text(f"❌ Xatolik yuz berdi: {exc}")
        return
    except Exception:  # noqa: BLE001
        logger.exception("Kutilmagan xatolik")
        await status_msg.edit_text("❌ Yuklab olishda kutilmagan xatolik yuz berdi.")
        return

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > config.max_file_size_mb:
        await status_msg.edit_text(
            f"❌ Fayl hajmi {file_size_mb:.1f}MB, bu ruxsat etilgan "
            f"{config.max_file_size_mb}MB limitidan katta."
        )
        os.remove(file_path)
        pending_links.pop(link_id, None)
        return

    input_file = FSInputFile(file_path)
    caption = title[:1000] if title else None

    try:
        if fmt == "video":
            await callback.message.answer_video(input_file, caption=caption)
        else:
            await callback.message.answer_audio(input_file, caption=caption)
        await status_msg.delete()
    finally:
        os.remove(file_path)
        pending_links.pop(link_id, None)
