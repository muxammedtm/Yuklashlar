import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import Config
from services import db, subscription

router = Router()
logger = logging.getLogger(__name__)


class AddChannel(StatesGroup):
    waiting_channel = State()
    waiting_invite = State()
    waiting_target = State()


def _is_admin(user_id: int, config: Config) -> bool:
    return user_id in config.admin_ids


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="adm:stats")],
            [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="adm:addch")],
            [InlineKeyboardButton(text="📋 Kanallar", callback_data="adm:listch")],
            [InlineKeyboardButton(text="⏯ Botni yoqish/o'chirish", callback_data="adm:toggle")],
        ]
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message, config: Config) -> None:
    if not _is_admin(message.from_user.id, config):
        return
    await message.answer("🛠 <b>Admin panel</b>", reply_markup=admin_menu())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, config: Config) -> None:
    if not _is_admin(message.from_user.id, config):
        return
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())


# ---------------- Statistika ----------------

@router.callback_query(F.data == "adm:stats")
async def adm_stats(callback: CallbackQuery, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        await callback.answer()
        return
    await callback.answer()

    users = await db.count_users()
    downloads = await db.get_setting("total_downloads") or "0"
    channels = await db.get_channels()
    active = sum(1 for c in channels if c["active"])
    enabled = (await db.get_setting("bot_enabled")) == "1"

    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"⬇️ Jami yuklashlar: <b>{downloads}</b>\n"
        f"📢 Kanallar: <b>{len(channels)}</b> (faol: {active})\n"
        f"⚙️ Bot holati: <b>{'🟢 yoqilgan' if enabled else '🔴 o‘chirilgan'}</b>"
    )
    await callback.message.edit_text(text, reply_markup=_back_menu())


def _back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:back")]]
    )


@router.callback_query(F.data == "adm:back")
async def adm_back(callback: CallbackQuery, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text("🛠 <b>Admin panel</b>", reply_markup=admin_menu())


# ---------------- Botni yoqish/o'chirish ----------------

@router.callback_query(F.data == "adm:toggle")
async def adm_toggle(callback: CallbackQuery, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        await callback.answer()
        return
    await callback.answer()
    enabled = (await db.get_setting("bot_enabled")) == "1"
    await db.set_setting("bot_enabled", "0" if enabled else "1")
    new_state = "🔴 o'chirildi" if enabled else "🟢 yoqildi"
    await callback.message.edit_text(
        f"⚙️ Bot {new_state}.", reply_markup=_back_menu()
    )


# ---------------- Kanal qo'shish (FSM) ----------------

@router.callback_query(F.data == "adm:addch")
async def adm_addch(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        await callback.answer()
        return
    await callback.answer()
    await state.set_state(AddChannel.waiting_channel)
    await callback.message.edit_text(
        "➕ <b>Kanal qo'shish</b>\n\n"
        "Quyidagilardan birini yuboring:\n"
        "1) Kanaldan biror postni <b>forward</b> qiling, yoki\n"
        "2) Ochiq kanal <code>@username</code> ini, yoki\n"
        "3) Kanalning <b>raqamli ID</b> sini (masalan <code>-1001234567890</code>).\n\n"
        "⚠️ Bot o'sha kanalda <b>admin</b> bo'lishi shart!\n\n"
        "💡 Yopiq kanal ID sini olish: kanaldan postni @getidsbot ga forward qiling.\n\n"
        "Bekor qilish: /cancel"
    )


@router.message(AddChannel.waiting_channel)
async def addch_receive(message: Message, state: FSMContext, bot: Bot, config: Config) -> None:
    if not _is_admin(message.from_user.id, config):
        return

    chat = None
    # 1) Forward qilingan post orqali (yopiq kanallar uchun ham ishlaydi)
    if getattr(message, "forward_origin", None) is not None:
        chat = getattr(message.forward_origin, "chat", None)
    if chat is None and getattr(message, "forward_from_chat", None) is not None:
        chat = message.forward_from_chat

    # 2) Raqamli ID orqali (-100... ko'rinishida) — yopiq kanallar uchun qulay
    if chat is None and message.text:
        raw = message.text.strip()
        # -100123... yoki 123... ko'rinishidagi ID
        if raw.lstrip("-").isdigit():
            try:
                chat = await bot.get_chat(int(raw))
            except Exception:  # noqa: BLE001
                await message.answer(
                    "❌ Bu ID bo'yicha kanal topilmadi.\n"
                    "ID to'g'ri ekanini va bot kanalda <b>admin</b> ekanini "
                    "tekshiring.\n\nBekor: /cancel"
                )
                return

    # 3) @username orqali
    if chat is None and message.text:
        uname = message.text.strip().lstrip("@")
        # t.me/username ko'rinishidan ham ajratamiz
        if "t.me/" in uname:
            uname = uname.split("t.me/")[-1].strip("/")
        # Taklif havolasi (+...) bu yerda ishlamaydi — ogohlantiramiz
        if uname.startswith("+"):
            await message.answer(
                "❌ Taklif havolasi (+...) orqali kanalni aniqlab bo'lmaydi.\n\n"
                "Yopiq kanal uchun quyidagilardan birini qiling:\n"
                "1) Kanaldan post <b>forward</b> qiling, yoki\n"
                "2) Kanalning <b>raqamli ID</b> sini yuboring "
                "(masalan <code>-1001234567890</code>).\n\n"
                "💡 ID ni olish: kanalga @username_to_id_bot kabi yordamchi "
                "botni qo'shing yoki kanaldan biror postni @getidsbot ga "
                "forward qiling.\n\nBekor: /cancel"
            )
            return
        try:
            chat = await bot.get_chat(f"@{uname}")
        except Exception:  # noqa: BLE001
            await message.answer(
                "❌ Kanal topilmadi. @username yoki raqamli ID yuboring, "
                "yoki kanaldan post forward qiling.\n\nBekor: /cancel"
            )
            return

    if chat is None or chat.type not in {"channel", "supergroup"}:
        await message.answer(
            "❌ Bu kanal/guruh emas. Kanaldan post forward qiling yoki "
            "@username yuboring.\n\nBekor: /cancel"
        )
        return

    # Bot kanalda adminmi? (obunachi sonini o'qib tekshiramiz)
    count = await subscription.get_member_count(bot, chat.id)
    if count is None:
        await message.answer(
            "❌ Botni avval shu kanalga <b>admin</b> qiling, keyin qaytadan urinib ko'ring.\n\n"
            "Bekor: /cancel"
        )
        return

    username = chat.username  # None bo'lishi mumkin (yopiq kanal)
    await state.update_data(
        chat_id=chat.id,
        username=username,
        title=chat.title,
        member_count=count,
    )

    if username:
        # Ochiq kanal — invite link avtomatik
        await state.update_data(invite_link=f"https://t.me/{username}")
        await state.set_state(AddChannel.waiting_target)
        await message.answer(
            f"✅ Kanal: <b>{chat.title}</b> (hozir {count} obunachi)\n\n"
            "Endi <b>obunachi limitini</b> yuboring (kanal shu songa yetganda "
            "majburiy obuna avtomatik o'chadi).\n"
            "Cheksiz bo'lsa <b>0</b> yuboring."
        )
    else:
        # Yopiq kanal — taklif havolasi kerak
        await state.set_state(AddChannel.waiting_invite)
        await message.answer(
            f"✅ Kanal: <b>{chat.title}</b> (hozir {count} obunachi)\n\n"
            "Bu yopiq kanal. Foydalanuvchilarga ko'rsatish uchun "
            "<b>taklif havolasini</b> (https://t.me/+...) yuboring."
        )


@router.message(AddChannel.waiting_invite)
async def addch_invite(message: Message, state: FSMContext, config: Config) -> None:
    if not _is_admin(message.from_user.id, config):
        return
    link = (message.text or "").strip()
    if not link.startswith("http"):
        await message.answer("❌ To'g'ri havola yuboring (https://t.me/+...).\n\nBekor: /cancel")
        return
    await state.update_data(invite_link=link)
    await state.set_state(AddChannel.waiting_target)
    await message.answer(
        "Endi <b>obunachi limitini</b> yuboring (yetganda majburiy obuna "
        "avtomatik o'chadi). Cheksiz bo'lsa <b>0</b> yuboring."
    )


@router.message(AddChannel.waiting_target)
async def addch_target(message: Message, state: FSMContext, config: Config) -> None:
    if not _is_admin(message.from_user.id, config):
        return
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("❌ Faqat son yuboring (masalan 345 yoki 0).\n\nBekor: /cancel")
        return

    target = int(raw)
    data = await state.get_data()
    await db.add_channel(
        chat_id=data["chat_id"],
        username=data.get("username"),
        invite_link=data.get("invite_link"),
        title=data.get("title"),
        target=target,
    )
    await state.clear()

    limit_text = "cheksiz" if target == 0 else f"{target} obunachi"
    await message.answer(
        f"✅ Kanal qo'shildi: <b>{data.get('title')}</b>\n"
        f"Limit: <b>{limit_text}</b>",
        reply_markup=admin_menu(),
    )


# ---------------- Kanallar ro'yxati ----------------

@router.callback_query(F.data == "adm:listch")
async def adm_listch(callback: CallbackQuery, bot: Bot, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        await callback.answer()
        return
    await callback.answer()

    channels = await db.get_channels()
    if not channels:
        await callback.message.edit_text(
            "📋 Hozircha kanal yo'q.", reply_markup=_back_menu()
        )
        return

    rows = []
    lines = ["📋 <b>Kanallar</b>\n"]
    for ch in channels:
        count = await subscription.get_member_count(bot, ch["chat_id"])
        count_str = str(count) if count is not None else "?"
        target_str = "∞" if not ch["target"] else str(ch["target"])
        status = "🟢" if ch["active"] else "🔴"
        name = ch["title"] or ch["username"] or str(ch["chat_id"])
        lines.append(f"{status} <b>{name}</b> — {count_str}/{target_str} obunachi")
        rows.append(
            [InlineKeyboardButton(
                text=f"🗑 {name}", callback_data=f"adm:delch:{ch['id']}"
            )]
        )

    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:back")])
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(F.data.startswith("adm:delch:"))
async def adm_delch(callback: CallbackQuery, bot: Bot, config: Config) -> None:
    if not _is_admin(callback.from_user.id, config):
        await callback.answer()
        return
    await callback.answer("O'chirildi")
    channel_id = int(callback.data.split(":")[2])
    await db.remove_channel(channel_id)
    # Ro'yxatni yangilab ko'rsatamiz
    await adm_listch(callback, bot, config)
