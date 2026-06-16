import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    download_dir: str
    max_file_size_mb: int
    admin_ids: list[int] = field(default_factory=list)


def _parse_admins(raw: str) -> list[int]:
    ids = []
    for part in raw.replace(" ", "").split(","):
        if part.isdigit():
            ids.append(int(part))
    return ids


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. BotHost panelida 'Bot Token' maydoniga "
            "tokenni kiriting (yoki .env faylida BOT_TOKEN=... ko'rsating)."
        )

    return Config(
        bot_token=token,
        download_dir=os.getenv("DOWNLOAD_DIR", "data/downloads"),
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "50")),
        # Admin Telegram ID'lari, vergul bilan: ADMIN_IDS=12345,67890
        admin_ids=_parse_admins(os.getenv("ADMIN_IDS", "")),
    )
