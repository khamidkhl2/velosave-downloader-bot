# VeloSave — Universal Social Media Downloader Bot

**VeloSave** ([@velo_save_bot](https://t.me/velo_save_bot)) is a high-speed Telegram bot for downloading media from Instagram, TikTok (without watermark), YouTube (Shorts & Videos up to 1080p), and Pinterest.

Part of the **Telegram Empire Network**, it seamlessly integrates with the shared user database, sponsor subscription verification gate, Telegram Stars VIP monetization, and sister bot cross-promotion.

---

## 🚀 Features

- **Multi-Platform Support**:
  - **Instagram**: Reels, Stories, Posts (video/photo).
  - **TikTok**: High-definition video with watermark removal.
  - **YouTube**: Shorts and long-form videos up to 1080p with combined audio.
  - **Pinterest**: Video pins and full-resolution images.
- **Strict File Size Verification**: Automatically verifies that media is $\le 50\text{ MB}$ (Telegram Bot API limit) before transmission.
- **Isolated Temporary Storage & Auto Cleanup**: Each download runs in an isolated directory with guaranteed cleanup to prevent disk bloat.
- **Clean Branded Captions**: Every downloaded video displays clean branding: `📥 Downloaded via @velo_save_bot` with zero author nicknames or scraper tags.
- **Monetization & Growth**:
  - **Sponsor Gate**: Enforces partner channel subscriptions for free users (VIPs bypass automatically).
  - **Telegram Stars VIP**: 30-day VIP pass purchased with Stars via native Telegram Invoices.
  - **Viral Referral System**: Users earn 30 days of VIP for inviting 3 friends.
  - **Alternating Follow-up Tips**: 1 in 2 videos sends a separate follow-up tip alternating between LumiChat (`@lumichat_ai_bot`) and Voxify (`@VoxifyVoiceBot`).
- **Multi-Language Support**: Fully localized in English (🇬🇧), Russian (🇷🇺), Uzbek (🇺🇿), and Spanish (🇪🇸).

---

## 📂 Project Structure

```
media-downloader-bot/
├── .env.example
├── Dockerfile
├── README.md
├── requirements.txt
├── config.py
├── main.py
├── handlers/
│   ├── __init__.py
│   ├── start.py        # /start, /help, /bots, /vip, /lang, /referral
│   ├── download.py     # URL detection, sponsor check, yt-dlp & sending
│   └── callbacks.py    # Language switch, sponsor verification, Stars payment
├── keyboards/
│   └── __init__.py
└── services/
    ├── __init__.py
    └── downloader.py   # yt-dlp + aiohttp downloader engine
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.10+
- `ffmpeg` installed on the system (required by `yt-dlp` to merge video and audio streams)

### 2. Environment Setup
```bash
cp .env.example .env
# Edit .env and supply your BOT_TOKEN from @BotFather
```

### 3. Local Run
```bash
pip install -r requirements.txt
python main.py
```

### 4. Docker Run
From the root repository (`tg_bots`):
```bash
docker build -t saveflow-bot -f media-downloader-bot/Dockerfile .
docker run -d --name saveflow --env-file media-downloader-bot/.env saveflow-bot
```

---

## 🤖 Bot Commands

- `/start` — Start the bot and see welcome message
- `/help` — Download instructions and supported platforms
- `/bots` — Discover other free bots in the network
- `/vip` — Buy 30-Day VIP Pass (Stars)
- `/lang` — Switch interface language
- `/referral` — View personal referral link and progress
