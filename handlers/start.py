from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

WELCOME_TEXT = (
    "🔥 Salom! Botga xush kelibsiz.\n\n"
    "Bot orqali quyidagilarni yuklab olishingiz mumkin:\n\n"
    "• Instagram — post va Reels (audio bilan)\n"
    "• TikTok — suv belgisiz video (audio bilan)\n"
    "• YouTube — video va Shorts (audio bilan)\n\n"
    "🚀 Yuklab olmoqchi bo'lgan videoga havolani shunchaki yuboring!\n"
    "😎 Bot guruhlarda ham ishlay oladi."
)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT)
