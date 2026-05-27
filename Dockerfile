FROM python:3.10-slim

WORKDIR /app

# System dependencies (FFmpeg, git, curl)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install latest yt-dlp first
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --upgrade yt-dlp

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the code
COPY . .

# Make start script executable
RUN chmod +x start

CMD ["bash", "start"]
