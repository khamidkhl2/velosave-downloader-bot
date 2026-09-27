FROM python:3.11-slim

# Install system dependencies including ffmpeg for audio/video merging
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY media-downloader-bot/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules and bot code
COPY shared /app/shared
COPY media-downloader-bot /app/media-downloader-bot

WORKDIR /app/media-downloader-bot

ENV PYTHONPATH="/app"

CMD ["python", "main.py"]
