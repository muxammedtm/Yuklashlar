from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from services import db
from services.i18n import t

router = Router()


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            ]
        ]
    )


def main_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Welcome xabari ostidagi «YouTube'dan qidirish» tugmasi.

    Bosilganda yo'riqnoma chiqadi: nusxalanadigan @vid yozuvi bilan.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "search_button"),
                    callback_data="yt_search",
                )
            ]
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await db.add_user(message.from_user.id)
    lang = await db.get_user_lang(message.from_user.id)

    if lang is None:
        # Birinchi marta — til tanlash
        await message.answer(t("uz", "choose_lang"), reply_markup=lang_keyboard())
        return

    await message.answer(t(lang, "welcome"), reply_markup=main_keyboard(lang))


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(callback: CallbackQuery) -> None:
    await callback.answer()
    lang = callback.data.split(":")[1]
    await db.set_user_lang(callback.from_user.id, lang)

    await callback.message.edit_text(t(lang, "lang_set"))
    await callback.message.answer(
        t(lang, "welcome"), reply_markup=main_keyboard(lang)
    )


@router.callback_query(F.data == "yt_search")
async def yt_search_guide(callback: CallbackQuery) -> None:
    await callback.answer()
    lang = await db.get_user_lang(callback.from_user.id) or "uz"
    await callback.message.answer(t(lang, "yt_guide"))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    lang = await db.get_user_lang(message.from_user.id) or "uz"
    await message.answer(t(lang, "help"))


@router.message(Command("til"))
async def cmd_lang(message: Message) -> None:
    await message.answer(t("uz", "choose_lang"), reply_markup=lang_keyboard())


# «Havola yuborish» tugmasi bosilganda — yo'naltiruvchi xabar
@router.message(F.text.in_({"📋 Havola yuborish", "📋 Отправить ссылку"}))
async def paste_prompt(message: Message) -> None:
    lang = await db.get_user_lang(message.from_user.id) or "uz"
    await message.answer(t(lang, "send_link_prompt"))
