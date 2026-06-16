import aiosqlite

DB_PATH = "data/bot.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                lang       TEXT DEFAULT 'uz',
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        # Majburiy obuna kanallari
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS channels (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id     INTEGER NOT NULL UNIQUE,
                username    TEXT,          -- ochiq kanal uchun (@siz)
                invite_link TEXT,          -- yopiq kanal uchun
                title       TEXT,
                target      INTEGER DEFAULT 0,  -- 0 = cheksiz
                active      INTEGER DEFAULT 1   -- 1 = majburiy obuna yoqilgan
            )
            """
        )
        # Kalit-qiymat sozlamalar
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        # Bot orqali obuna bo'lganlar (har kanal uchun, takrorlanmaydi)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS referrals (
                channel_id INTEGER NOT NULL,
                user_id    INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (channel_id, user_id)
            )
            """
        )
        await db.commit()

        await _set_default(db, "total_downloads", "0")
        await _set_default(db, "bot_enabled", "1")
        await db.commit()


async def _set_default(db: aiosqlite.Connection, key: str, value: str) -> None:
    await db.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value)
    )


# ---------------- Foydalanuvchilar ----------------

async def add_user(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,)
        )
        await db.commit()


async def get_user_lang(user_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT lang FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def set_user_lang(user_id: int, lang: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (user_id, lang) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET lang = excluded.lang",
            (user_id, lang),
        )
        await db.commit()


async def count_users() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


# ---------------- Kanallar (majburiy obuna) ----------------

async def add_channel(
    chat_id: int,
    username: str | None,
    invite_link: str | None,
    title: str | None,
    target: int,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO channels (chat_id, username, invite_link, title, target, active)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(chat_id) DO UPDATE SET
                username = excluded.username,
                invite_link = excluded.invite_link,
                title = excluded.title,
                target = excluded.target,
                active = 1
            """,
            (chat_id, username, invite_link, title, target),
        )
        await db.commit()


async def remove_channel(channel_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        await db.execute("DELETE FROM referrals WHERE channel_id = ?", (channel_id,))
        await db.commit()


async def get_channels(active_only: bool = False) -> list[dict]:
    query = "SELECT id, chat_id, username, invite_link, title, target, active FROM channels"
    if active_only:
        query += " WHERE active = 1"
    query += " ORDER BY id"
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(query) as cur:
            rows = await cur.fetchall()
            return [
                {
                    "id": r[0],
                    "chat_id": r[1],
                    "username": r[2],
                    "invite_link": r[3],
                    "title": r[4],
                    "target": r[5],
                    "active": r[6],
                }
                for r in rows
            ]


async def deactivate_channel(channel_id: int) -> None:
    """Kanalni majburiy obunadan o'chiradi (lekin ro'yxatda qoldiradi)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE channels SET active = 0 WHERE id = ?", (channel_id,)
        )
        await db.commit()


# ---------------- Referrallar (bot orqali obuna bo'lganlar) ----------------

async def add_referral(channel_id: int, user_id: int) -> bool:
    """Bot orqali obunani qayd qiladi.

    Yangi qo'shilsa True, allaqachon mavjud bo'lsa False qaytaradi.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT OR IGNORE INTO referrals (channel_id, user_id) VALUES (?, ?)",
            (channel_id, user_id),
        )
        await db.commit()
        return cur.rowcount > 0


async def count_referrals(channel_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM referrals WHERE channel_id = ?", (channel_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


# ---------------- Sozlamalar ----------------

async def get_setting(key: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def set_setting(key: str, value: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        await db.commit()


async def increment_downloads() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE settings SET value = CAST(value AS INTEGER) + 1 "
            "WHERE key = 'total_downloads'"
        )
        await db.commit()
        async with db.execute(
            "SELECT value FROM settings WHERE key = 'total_downloads'"
        ) as cur:
            row = await cur.fetchone()
            return int(row[0]) if row else 0
