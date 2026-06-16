import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from services import db

logger = logging.getLogger(__name__)

# Obuna bo'lgan deb hisoblanadigan holatlar
SUBSCRIBED_STATUSES = {"member", "administrator", "creator"}


async def is_subscribed(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Foydalanuvchi kanalga a'zo ekanini tekshiradi."""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in SUBSCRIBED_STATUSES
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        # Bot kanalda admin emas yoki kanal topilmadi — tekshira olmaymiz.
        logger.warning("A'zolikni tekshirib bo'lmadi (%s): %s", chat_id, exc)
        return True  # tekshira olmasak, foydalanuvchini bloklamaymiz


async def get_member_count(bot: Bot, chat_id: int) -> int | None:
    try:
        return await bot.get_chat_member_count(chat_id)
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        logger.warning("Obunachi sonini olib bo'lmadi (%s): %s", chat_id, exc)
        return None


async def get_unsubscribed(bot: Bot, user_id: int) -> list[dict]:
    """Foydalanuvchi obuna bo'lmagan faol kanallar ro'yxatini qaytaradi.

    Shu bilan birga har bir faol kanal target'ga yetgan bo'lsa — uni
    majburiy obunadan avtomatik o'chiradi va adminlarga xabar berish
    uchun ro'yxat to'playdi (auto_disabled).
    """
    channels = await db.get_channels(active_only=True)
    not_subscribed = []

    for ch in channels:
        # Target tekshiruvi (obunachi soniga yetdimi?)
        if ch["target"] and ch["target"] > 0:
            count = await get_member_count(bot, ch["chat_id"])
            if count is not None and count >= ch["target"]:
                await db.deactivate_channel(ch["id"])
                logger.info(
                    "Kanal target'ga yetdi, o'chirildi: %s (%s/%s)",
                    ch["title"], count, ch["target"],
                )
                _auto_disabled.append({**ch, "count": count})
                continue  # bu kanal endi majburiy emas

        # A'zolik tekshiruvi
        if not await is_subscribed(bot, ch["chat_id"], user_id):
            not_subscribed.append(ch)

    return not_subscribed


# Auto-o'chirilgan kanallar haqida adminlarga xabar berish uchun navbat.
# Handler tekshirgandan keyin bu ro'yxatni o'qib, tozalaydi.
_auto_disabled: list[dict] = []


def pop_auto_disabled() -> list[dict]:
    global _auto_disabled
    items = _auto_disabled
    _auto_disabled = []
    return items
