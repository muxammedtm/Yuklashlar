import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # lokal/VPS uchun .env; BotHost'da panel orqali kiritilgan
# o'zgaruvchilar konteynerga avtomatik in'ektsiya qilinadi, .env shart emas


@dataclass
class Config:
    bot_token: str
    download_dir: str
    max_file_size_mb: int


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. BotHost panelida bot yaratishda 'Bot Token' "
            "maydoniga BotFather'dan olingan tokenni kiriting (yoki lokal "
            "ishga tushirishda .env faylida BOT_TOKEN=... ko'rsating)."
        )

    return Config(
        bot_token=token,
        # data/ papkasi BotHost'da persistent va yoziladigan papka hisoblanadi
        download_dir=os.getenv("DOWNLOAD_DIR", "data/downloads"),
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "50")),
    )
