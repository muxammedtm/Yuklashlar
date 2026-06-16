import asyncio
import logging
import os
import re
import uuid

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import Config
from services import db, subscription
from services.downloader import DownloadError, download_media, extract_info
from services.i18n import t

router = Router()
logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"(https?://\S+)")
URL_SEND_LIMIT_MB = 20

# Status xabarini "jonli" o'zgartirish orasidagi pauza (Telegram flood'dan
# qochish uchun). Sekundiga ~1 marta tahrir xavfsiz.
MORPH_DELAY = 0.6


async def _morph(status: Message, text: str, delay: float = MORPH_DELAY) -> None:
    """Status xabarini yangi matnga 'parchalanish' effekti bilan o'zgartiradi.

    Telegram bitta xabarni edit qilganda harflarni almashtirib, tabiiy
    morfing animatsiyasini ko'rsatadi. Orasiga pauza qo'yamiz.
    """
    try:
        await status.edit_text(text)
        await asyncio.sleep(delay)
    except TelegramBadRequest:
        # Matn bir xil bo'lsa yoki tez-tez tahrir bo'lsa — e'tiborsiz qoldiramiz
        pass

pending_links: dict[str, str] = {}

PLATFORM_NAMES = {"instagram": "Instagram", "tiktok": "TikTok", "youtube": "YouTube"}


def detect_platform(url: str) -> str | None:
    url = url.lower()
    if "instagram.com" in url:
        return "instagram"
    if "tiktok.com" in url:
        return "tiktok"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return None


def format_keyboard(lang: str, link_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_fast"), callback_data=f"dl:fast:{link_id}"),
                InlineKeyboardButton(text=t(lang, "btn_best"), callback_data=f"dl:best:{link_id}"),
            ],
            [InlineKeyboardButton(text=t(lang, "btn_audio"), callback_data=f"dl:audio:{link_id}")],
        ]
    )


def subscribe_text(lang: str, channels: list[dict]) -> str:
    """Majburiy obuna xabari + kanal nomlari ro'yxati."""
    lines = [t(lang, "must_subscribe"), ""]
    for i, ch in enumerate(channels, 1):
        name = ch["title"] or ch["username"] or "Kanal"
        lines.append(f"{i}. 📢 <b>{name}</b>")
    return "\n".join(lines)


def subscribe_keyboard(lang: str, channels: list[dict], link_id: str) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        url = ch["invite_link"] or (f"https://t.me/{ch['username']}" if ch["username"] else None)
        if url:
            name = ch["title"] or ch["username"] or "Kanal"
            rows.append([InlineKeyboardButton(text=f"📢 {name}", url=url)])
    rows.append([InlineKeyboardButton(text=t(lang, "check_subscribe"), callback_data=f"sub:{link_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _notify_auto_disabled(bot: Bot, config: Config) -> None:
    """Target'ga yetib o'chirilgan kanallar haqida adminlarga xabar."""
    items = subscription.pop_auto_disabled()
    for ch in items:
        name = ch["title"] or ch["username"] or str(ch["chat_id"])
        text = (
            f"🎯 <b>Kanal limitga yetdi!</b>\n\n"
            f"📢 {name}\n"
            f"👥 {ch['count']}/{ch['target']} obunachi\n\n"
            "Majburiy obuna bu kanaldan avtomatik o'chirildi."
        )
        for admin_id in config.admin_ids:
            try:
                await bot.send_message(admin_id, text)
            except Exception:  # noqa: BLE001
                pass


async def _check_gate(message: Message, user_id: int, bot: Bot, config: Config, lang: str, link_id: str) -> bool:
    """Bot holati + majburiy obunani tekshiradi. O'tsa True qaytaradi."""
    # Bot o'chirilganmi?
    if (await db.get_setting("bot_enabled")) != "1":
        await message.answer(t(lang, "bot_disabled"))
        return False

    unsub = await subscription.get_unsubscribed(bot, user_id)
    await _notify_auto_disabled(bot, config)

    if unsub:
        await message.answer(
            subscribe_text(lang, unsub),
            reply_markup=subscribe_keyboard(lang, unsub, link_id),
        )
        return False
    return True


@router.message(F.text.regexp(URL_PATTERN))
async def handle_link(message: Message, bot: Bot, config: Config) -> None:
    match = URL_PATTERN.search(message.text or "")
    if not match:
        return

    lang = await db.get_user_lang(message.from_user.id) or "uz"
    url = match.group(1)
    platform = detect_platform(url)

    if platform is None:
        await message.answer(t(lang, "unsupported"))
        return

    link_id = uuid.uuid4().hex[:8]
    pending_links[link_id] = url

    if not await _check_gate(message, message.from_user.id, bot, config, lang, link_id):
        return

    await message.answer(t(lang, "choose_format"), reply_markup=format_keyboard(lang, link_id))


@router.callback_query(F.data.startswith("sub:"))
async def recheck_sub(callback: CallbackQuery, bot: Bot, config: Config) -> None:
    lang = await db.get_user_lang(callback.from_user.id) or "uz"
    link_id = callback.data.split(":")[1]

    # confirm_and_count: obuna bo'lganlarni sanaydi + target'ni tekshiradi
    still_missing = await subscription.confirm_and_count(bot, callback.from_user.id)
    await _notify_auto_disabled(bot, config)

    if still_missing:
        await callback.answer(t(lang, "not_subscribed"), show_alert=True)
        return

    await callback.answer(t(lang, "subscribed_ok"))
    if link_id in pending_links:
        await callback.message.edit_text(
            t(lang, "choose_format"), reply_markup=format_keyboard(lang, link_id)
        )
    else:
        await callback.message.edit_text(t(lang, "subscribed_ok"))


async def _send_via_url(message: Message, url: str, status: Message, lang: str) -> bool:
    await _morph(status, t(lang, "step_checking"))
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
        await _morph(status, t(lang, "step_found"))
        await _morph(status, t(lang, "step_sending"))
        try:
            await message.answer_video(direct_url, caption=caption)
            await status.delete()
            return True
        except TelegramBadRequest as exc:
            logger.info("URL bilan yuborib bo'lmadi: %s", exc)
    return False


async def _download_and_send(message: Message, url: str, fmt: str, status: Message, config: Config, lang: str) -> None:
    await _morph(status, t(lang, "step_downloading"))
    try:
        file_path, title = await download_media(url, fmt, config.download_dir)
    except DownloadError:
        await status.edit_text(t(lang, "error"))
        return
    except Exception:  # noqa: BLE001
        logger.exception("download_media xatosi")
        await status.edit_text(t(lang, "error"))
        return

    try:
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > config.max_file_size_mb:
            await status.edit_text(t(lang, "too_big", size=size_mb, limit=config.max_file_size_mb))
            return
        await _morph(status, t(lang, "step_sending"))
        caption = title[:1000] if title else None
        if fmt == "audio":
            await message.answer_audio(FSInputFile(file_path), caption=caption)
        else:
            await message.answer_video(FSInputFile(file_path), caption=caption)
        await status.delete()
        await db.increment_downloads()
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.callback_query(F.data.startswith("dl:"))
async def handle_choice(callback: CallbackQuery, bot: Bot, config: Config) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return

    lang = await db.get_user_lang(callback.from_user.id) or "uz"
    _, fmt, link_id = callback.data.split(":")
    url = pending_links.get(link_id)
    if not url:
        await callback.message.edit_text(t(lang, "link_expired"))
        return

    # Xavfsizlik: yana bir bor obunani tekshiramiz
    if (await db.get_setting("bot_enabled")) != "1":
        await callback.message.edit_text(t(lang, "bot_disabled"))
        return
    unsub = await subscription.get_unsubscribed(bot, callback.from_user.id)
    await _notify_auto_disabled(bot, config)
    if unsub:
        await callback.message.edit_text(
            subscribe_text(lang, unsub),
            reply_markup=subscribe_keyboard(lang, unsub, link_id),
        )
        return

    status = await callback.message.edit_text(t(lang, "preparing"))

    if fmt == "fast":
        if await _send_via_url(callback.message, url, status, lang):
            await db.increment_downloads()
            pending_links.pop(link_id, None)
            return

    await _download_and_send(callback.message, url, fmt, status, config, lang)
    pending_links.pop(link_id, None)
