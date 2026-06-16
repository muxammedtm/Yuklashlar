import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import load_config
from handlers import admin, download, start
from services import db
from services.ffmpeg_setup import setup_ffmpeg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()
    os.makedirs(config.download_dir, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # Ma'lumotlar bazasini tayyorlash
    await db.init_db()
    logger.info("Ma'lumotlar bazasi tayyor")

    # ffmpeg/ffprobe tayyorlash
    logger.info("ffmpeg tayyorlanmoqda...")
    await asyncio.to_thread(setup_ffmpeg)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # config'ni barcha handlerlarga yetkazib berish
    dp["config"] = config

    # Routerlar tartibi muhim: admin va start (komandalar) avval, download keyin
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(download.router)

    await bot.delete_webhook(drop_pending_updates=True)

    # Bosh menyu (ko'k "Menu" tugmasi ostidagi komandalar)
    await bot.set_my_commands([
        BotCommand(command="start", description="🔄 Boshlash / Старт"),
        BotCommand(command="help", description="ℹ️ Yordam / Помощь"),
        BotCommand(command="til", description="🌐 Til / Язык"),
    ])

    logger.info("Bot ishga tushdi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
