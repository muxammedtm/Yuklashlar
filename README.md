# Instagram / TikTok / YouTube Yuklab Olish Boti (BotHost.ru uchun)

Python + aiogram 3 + yt-dlp asosida qurilgan Telegram bot. Instagram, TikTok va
YouTube havolalarini video yoki mp3 (audio) shaklida yuklab olib beradi.
Quyidagi qo'llanma maxsus [bothost.ru](https://bothost.ru) хостингига
joylashtirish uchun yozilgan.

## 1. BotFather'dan token olish

1. Telegramda [@BotFather](https://t.me/BotFather) ga yozing.
2. `/newbot` buyrug'ini yuboring, botga nom va username bering.
3. Beriladigan tokenni saqlab qo'ying — BotHost formasida kerak bo'ladi.

## 2. Kodni GitHub'ga yuklash

BotHost botni **Git repozitoriyasi** orqali deploy qiladi (ZIP yuklash emas).
Shu sabab avval kodni GitHub'ga (yoki GitLab'ga) yuklashingiz kerak:

```bash
cd insta_tiktok_yt_bot
git init
git add .
git commit -m "Boshlang'ich versiya"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO_NOMI.git
git push -u origin main
```

> Repozitoriya **public** bo'lsa, hech qanday qo'shimcha sozlamasiz ishlaydi.
> Private repo ishlatmoqchi bo'lsangiz, BotHost panelidagi "Git
> repozitoriyalar" bo'limida Personal Access Token orqali ulashingiz kerak
> bo'ladi.

`.env` fayli **hech qachon** repoga tushmasligi kerak — `.gitignore` ichida
allaqachon shu qatori bor.

## 3. BotHost'da bot yaratish

1. [bothost.ru/register](https://bothost.ru/register) orqali ro'yxatdan o'ting.
2. Panelda **"Создать бота"** tugmasini bosing.
3. Formani to'ldiring:
   - **Название бота**: ixtiyoriy nom
   - **Платформа**: Telegram
   - **Библиотека**: Aiogram 3.x
   - **Bot Token**: BotFather'dan olingan token
   - **Git URL**: `https://github.com/USERNAME/REPO_NOMI.git`
   - **Ветка**: `main`
   - **Главный файл** (qo'shimcha sozlamalarda bo'lsa): `main.py`
4. **"Создать бота"** tugmasini bosing — tizim avtomatik ravishda
   repozitoriyani kloplaydi, `Dockerfile`'ni topib (ffmpeg shu yerda
   o'rnatiladi) imageni qurib, botni ishga tushiradi (odatda 2-5 daqiqa).

## 4. Ishga tushganini tekshirish

- Panelda **"Логи работы"** bo'limini oching — `Bot ishga tushdi` degan
  qatorni ko'rsangiz, hammasi joyida.
- Telegramda botga `/start` yuboring, so'ng Instagram/TikTok/YouTube
  havolasini tashlab ko'ring.
- Xatolik bo'lsa, avval **"Логи сборки"** (build loglari), keyin
  **"Логи работы"** (runtime loglari) ni tekshiring.

## 5. Kodni keyinroq yangilash

Bepul tarifda yangilanish qo'lda amalga oshiriladi:

1. GitHub'ga yangi commit push qiling.
2. BotHost panelida bot sahifasida **"Обновить из Git"** tugmasini bosing.

(Pullik tariflarda GitHub webhook orqali avtomatik yangilanish ham mavjud.)

## Muhim eslatmalar

- **Bepul tarif cheklovlari**: 1 bot, faqat Long Polling (webhook emas) —
  bizning bot aynan polling (`start_polling`) ishlatadi, shuning uchun
  bepul tarifga to'liq mos keladi.
- **Doimiy xotira**: BotHost'da `/app/data` papkasi har bir yangilanishdan
  keyin ham saqlanadi (Git bilan ustidan yozilmaydi). Shu sabab yuklab
  olingan vaqtinchalik fayllar ham `data/downloads` papkasiga tushadi —
  lekin bot har bir faylni yuborgandan keyin o'zi o'chirib turadi, shu
  sabab joy tugashidan xavotirlanmang.
- **Fayl hajmi limiti**: Oddiy Telegram Bot API orqali bot yubora oladigan
  faylning maksimal hajmi ~50MB. Bu BotHost'ning emas, Telegramning o'zining
  cheklovi.
- **Instagram cheklovlari**: Instagram ba'zi postlar (private akkauntlar
  yoki ba'zi reels) uchun login talab qilishi mumkin. Bunday holatda
  brauzerdan eksport qilingan `cookies.txt` faylini BotHost fayl
  menejeri orqali `data/` papkasiga yuklab, `services/downloader.py`
  ichidagi `cookiefile` qatorini yoqishingiz kerak bo'ladi.
- **Mualliflik huquqi**: Botdan faqat o'ziga tegishli yoki yuklab olishga
  ruxsat berilgan video/audio kontent uchun foydalanilishini tavsiya
  qilamiz.

## Keyingi qadamlar (xohlasangiz qo'shib beraman)

- Pinterest, Threads, Snapchat, Likee qo'llab-quvvatlashi
- Shazam funksiyasi (qo'shiq nomi/ijrochi, video/audio orqali musiqa aniqlash)
  — `shazamio` kutubxonasi orqali qo'shiladi
- Guruhlarda ishlashi uchun qo'shimcha sozlamalar (admin tekshiruvi va h.k.)
- Yuklab olishlar sonini cheklash / statistika (SQLite, `data/bot.db`)
