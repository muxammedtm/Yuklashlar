import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import load_config
from handlers import download, start
from services.ffmpeg_setup import setup_ffmpeg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()
    os.makedirs(config.download_dir, exist_ok=True)

    # ffmpeg/ffprobe ni tayyorlaymiz (birinchi marta yuklab olinadi)
    logger.info("ffmpeg tayyorlanmoqda...")
    await asyncio.to_thread(setup_ffmpeg)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # config'ni barcha handlerlarga avtomatik tarzda yetkazib berish
    dp["config"] = config

    dp.include_router(start.router)
    dp.include_router(download.router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot ishga tushdi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
