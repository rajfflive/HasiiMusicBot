FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg git curl && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install --upgrade yt-dlp

# yt-dlp config to fix format error
RUN mkdir -p /root/.config/yt-dlp && \
    echo "-f bestaudio[ext=m4a]/bestaudio" > /root/.config/yt-dlp/config.txt && \
    echo "--no-playlist" >> /root/.config/yt-dlp/config.txt

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start

CMD ["bash", "start"]
