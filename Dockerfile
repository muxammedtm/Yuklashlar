FROM python:3.11-slim

WORKDIR /app

# yt-dlp video/audio formatlarni birlashtirish va mp3'ga o'girish uchun
# ffmpeg'ga muhtoj — standart avto-build buni o'rnatmaydi, shu sabab
# alohida Dockerfile ishlatamiz
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
