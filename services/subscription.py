import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from services import db

logger = logging.getLogger(__name__)

SUBSCRIBED_STATUSES = {"member", "administrator", "creator"}

# Foydalanuvchi qaysi kanallarga obuna bo'lishi so'ralganini (vaqtincha)
# eslab turamiz. Shu bilan faqat bot "haydagan" obunalarni sanaymiz.
# user_id -> {channel_id, ...}
_prompted: dict[int, set[int]] = {}

# Target'ga yetib o'chirilgan kanallar (adminlarga xabar berish uchun)
_auto_disabled: list[dict] = []


async def is_subscribed(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in SUBSCRIBED_STATUSES
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        logger.warning("A'zolikni tekshirib bo'lmadi (%s): %s", chat_id, exc)
        return True  # tekshira olmasak, bloklamaymiz


async def get_member_count(bot: Bot, chat_id: int) -> int | None:
    try:
        return await bot.get_chat_member_count(chat_id)
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        logger.warning("Obunachi sonini olib bo'lmadi (%s): %s", chat_id, exc)
        return None


async def get_unsubscribed(bot: Bot, user_id: int) -> list[dict]:
    """Foydalanuvchi obuna bo'lmagan faol kanallarni qaytaradi.

    Shu kanallarni 'so'ralgan' deb belgilab qo'yadi (keyin obuna bo'lsa
    sanash uchun).
    """
    channels = await db.get_channels(active_only=True)
    not_subscribed = []
    for ch in channels:
        if not await is_subscribed(bot, ch["chat_id"], user_id):
            not_subscribed.append(ch)

    if not_subscribed:
        _prompted[user_id] = {c["id"] for c in not_subscribed}
    return not_subscribed


async def confirm_and_count(bot: Bot, user_id: int) -> list[dict]:
    """«Tekshirish» bosilganda chaqiriladi.

    So'ralgan kanallardan endi obuna bo'lganlarini sanaydi (referral),
    target'ga yetganini avtomatik o'chiradi. Hali obuna bo'lmaganlar
    ro'yxatini qaytaradi.
    """
    channels = await db.get_channels(active_only=True)
    user_prompted = _prompted.get(user_id, set())
    still_missing = []

    for ch in channels:
        subscribed = await is_subscribed(bot, ch["chat_id"], user_id)
        if subscribed:
            # Faqat bot so'ragan kanal bo'lsa sanaymiz
            if ch["id"] in user_prompted:
                newly = await db.add_referral(ch["id"], user_id)
                user_prompted.discard(ch["id"])
                if newly and ch["target"] and ch["target"] > 0:
                    cnt = await db.count_referrals(ch["id"])
                    if cnt >= ch["target"]:
                        await db.deactivate_channel(ch["id"])
                        logger.info(
                            "Kanal target'ga yetdi: %s (%s/%s)",
                            ch["title"], cnt, ch["target"],
                        )
                        _auto_disabled.append({**ch, "count": cnt})
        else:
            still_missing.append(ch)

    _prompted[user_id] = user_prompted
    return still_missing


def pop_auto_disabled() -> list[dict]:
    global _auto_disabled
    items = _auto_disabled
    _auto_disabled = []
    return items
