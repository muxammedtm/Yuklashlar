TEXTS = {
    "uz": {
        "choose_lang": "🌐 Tilni tanlang / Выберите язык:",
        "lang_set": "✅ Til o'zbekchaga o'rnatildi.",
        "welcome": (
            "🔥 Salom! Botga xush kelibsiz.\n\n"
            "Bot orqali quyidagilarni yuklab olishingiz mumkin:\n\n"
            "• Instagram — post va Reels\n"
            "• TikTok — suv belgisiz video\n"
            "• YouTube — video va Shorts\n\n"
            "🚀 Yuklab olmoqchi bo'lgan videoga havolani yuboring!"
        ),
        "help": (
            "ℹ️ <b>Yordam</b>\n\n"
            "1. Instagram, TikTok yoki YouTube'dan havolani nusxalang.\n"
            "2. Havolani shu yerga yuboring.\n"
            "3. Format tanlang:\n"
            "   ⚡️ Video (tez) — darhol keladi\n"
            "   💎 Video (sifatli) — 720p, tiniqroq\n"
            "   🎵 Audio (mp3) — faqat ovoz\n\n"
            "📋 «Havola yuborish» tugmasi orqali ham yuborishingiz mumkin.\n\n"
            "Til o'zgartirish: /til"
        ),
        "paste_button": "📋 Havola yuborish",
        "send_link_prompt": "🔗 Instagram / TikTok / YouTube havolasini yuboring:",
        "unsupported": (
            "❗️ Bu havola qo'llab-quvvatlanmaydi.\n"
            "Faqat Instagram, TikTok va YouTube havolalarini qabul qilaman."
        ),
        "choose_format": "✅ Havola qabul qilindi. Qaysi formatda?",
        "btn_fast": "⚡️ Video (tez)",
        "btn_best": "💎 Video (sifatli)",
        "btn_audio": "🎵 Audio (mp3)",
        "preparing": "⏳ Tayyorlanmoqda...",
        "downloading": "⏳ Yuklab olinmoqda...",
        "step_checking": "🔍 Havola tekshirilmoqda...",
        "step_found": "✅ Video topildi!",
        "step_downloading": "⬇️ Yuklab olinmoqda...",
        "step_sending": "📤 Yuborilmoqda...",
        "error": "❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.",
        "too_big": (
            "❌ Fayl hajmi {size:.1f}MB — Telegram limiti ({limit}MB) dan katta.\n"
            "⚡️ Video (tez) variantni sinab ko'ring."
        ),
        "link_expired": "❌ Havola muddati tugagan. Qaytadan yuboring.",
        "bot_disabled": "🚧 Bot vaqtincha texnik ishlar tufayli to'xtatilgan.",
        # Majburiy obuna
        "must_subscribe": (
            "📢 Botdan foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling:"
        ),
        "check_subscribe": "✅ Tekshirish",
        "not_subscribed": "❗️ Hali hammasiga obuna bo'lmadingiz. Tekshiring va qayta bosing.",
        "subscribed_ok": "✅ Rahmat! Endi havola yuborishingiz mumkin.",
    },
    "ru": {
        "choose_lang": "🌐 Tilni tanlang / Выберите язык:",
        "lang_set": "✅ Язык установлен на русский.",
        "welcome": (
            "🔥 Привет! Добро пожаловать в бота.\n\n"
            "С помощью бота вы можете скачивать:\n\n"
            "• Instagram — посты и Reels\n"
            "• TikTok — видео без водяных знаков\n"
            "• YouTube — видео и Shorts\n\n"
            "🚀 Отправьте ссылку на видео, которое хотите скачать!"
        ),
        "help": (
            "ℹ️ <b>Помощь</b>\n\n"
            "1. Скопируйте ссылку из Instagram, TikTok или YouTube.\n"
            "2. Отправьте ссылку сюда.\n"
            "3. Выберите формат:\n"
            "   ⚡️ Видео (быстро) — приходит сразу\n"
            "   💎 Видео (качество) — 720p, чётче\n"
            "   🎵 Аудио (mp3) — только звук\n\n"
            "📋 Можно также через кнопку «Отправить ссылку».\n\n"
            "Сменить язык: /til"
        ),
        "paste_button": "📋 Отправить ссылку",
        "send_link_prompt": "🔗 Отправьте ссылку Instagram / TikTok / YouTube:",
        "unsupported": (
            "❗️ Эта ссылка не поддерживается.\n"
            "Принимаю только ссылки Instagram, TikTok и YouTube."
        ),
        "choose_format": "✅ Ссылка принята. В каком формате?",
        "btn_fast": "⚡️ Видео (быстро)",
        "btn_best": "💎 Видео (качество)",
        "btn_audio": "🎵 Аудио (mp3)",
        "preparing": "⏳ Готовится...",
        "downloading": "⏳ Скачивается...",
        "step_checking": "🔍 Проверяю ссылку...",
        "step_found": "✅ Видео найдено!",
        "step_downloading": "⬇️ Скачиваю...",
        "step_sending": "📤 Отправляю...",
        "error": "❌ Произошла ошибка. Попробуйте позже.",
        "too_big": (
            "❌ Размер файла {size:.1f}MB — больше лимита Telegram ({limit}MB).\n"
            "⚡️ Попробуйте вариант Видео (быстро)."
        ),
        "link_expired": "❌ Срок ссылки истёк. Отправьте заново.",
        "bot_disabled": "🚧 Бот временно остановлен на технические работы.",
        "must_subscribe": (
            "📢 Чтобы пользоваться ботом, подпишитесь на канал(ы):"
        ),
        "check_subscribe": "✅ Проверить",
        "not_subscribed": "❗️ Вы ещё не подписаны на все. Проверьте и нажмите снова.",
        "subscribed_ok": "✅ Спасибо! Теперь можете отправлять ссылку.",
    },
}


def t(lang: str | None, key: str, **kwargs) -> str:
    """Berilgan til va kalit bo'yicha matnni qaytaradi (standart: uz)."""
    lang = lang if lang in TEXTS else "uz"
    text = TEXTS[lang].get(key) or TEXTS["uz"].get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
