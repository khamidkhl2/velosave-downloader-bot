# 🤝 Project Handoff: VeloSave Downloader Bot

This document contains everything needed to resume, maintain, and scale **VeloSave** ([@velo_save_bot](https://t.me/velo_save_bot)).

---

## 📌 Executive Summary & Key Credentials

| Property | Value |
| :--- | :--- |
| **Bot Name** | `VeloSave` |
| **Telegram Handle** | **`@velo_save_bot`** |
| **Bot ID** | `8773204325` |
| **Bot Token** | `8773204325:AAEe5by3DRBi2SkGvG-coNLHwFRa9TclNH0` |
| **Owner / Admin ID** | `5831301324` |
| **GitHub Repository** | [github.com/khamidkhl2/velosave-downloader-bot](https://github.com/khamidkhl2/velosave-downloader-bot) |
| **Live Webhook URL** | `https://velosave-downloader-bot.vercel.app/` |
| **Local Project Path** | `/Users/khamid/Documents/tg_bots/media-downloader-bot` |
| **Deployment Platform**| Vercel Serverless (Python 3.11) |

---

## 🚀 Current System Status

* **Status:** ✅ **LIVE & FULLY OPERATIONAL**
* **Deployment Workflow:** Connected to GitHub `main` branch. Any `git push` automatically redeploys on Vercel within ~20 seconds.
* **Telegram Webhook:** Configured and active. Updates are delivered instantly to `https://velosave-downloader-bot.vercel.app/`.
* **Profile Picture:** Configured with a clean, flat 2D vector app icon (solid royal blue background with a white download arrow and video play icon).

---

## 🛠️ Key Handlers & Logic

### 1. Media Downloader Pipeline (`handlers/download.py`)
- Detects URLs from Instagram (Reels/Stories/Posts), TikTok (no watermark), YouTube (Shorts/1080p), and Pinterest using `services/downloader.py` (`yt-dlp` engine).
- **Caption Formatting**:
  - All author nicknames, scraped titles, and `video by [BLANK]` artifacts are completely stripped.
  - Caption is strictly:
    ```html
    📥 <b>Downloaded via @velo_save_bot</b>
    ```
- **1-in-2 Alternating Separate Tip**:
  - The cross-promotion tip is sent as a **separate message** rather than attached to the video.
  - Only sent on **every second video** (`dl_count % 2 == 0`).
  - Alternates deterministically between **LumiChat** and **Voxify Voice**:
    - Download #2: `💡 Tip: Want to ask questions, write essays or solve homework? Try @lumichat_ai_bot`
    - Download #4: `💡 Tip: Want to voice text with realistic AI speech? Try @VoxifyVoiceBot`

### 2. Monetization & Gating
- **Sponsor Gate**: Unsubscribed users must join required partner channels before downloads proceed.
- **Stars VIP Pass**: Users can purchase 30-day VIP pass for 50 Telegram Stars (`/vip`).
- **Viral Referrals**: Inviting 3 friends grants 30 days of VIP for free (`/referral`).

---

## 📁 Repository Structure

```text
media-downloader-bot/
├── api/
│   └── index.py            # Vercel Serverless function entry point
├── assets/
│   └── logo.jpg            # Clean 2D flat minimalist profile icon
├── handlers/
│   ├── download.py         # URL regex handler, yt-dlp downloader, clean caption & separate tip
│   ├── start.py            # /start, /help, /bots, /lang, /vip, /referral
│   ├── callbacks.py        # Language switches, sponsor verification, Stars payment
│   └── sponsor_gate.py     # Channel subscription check
├── keyboards/
│   └── inline.py           # Inline action keyboards
├── services/
│   └── downloader.py       # yt-dlp wrapper with 50MB file size checks & temp directory cleanup
├── shared/                 # Symlinked/synchronized core shared modules
├── config.py               # Downloader bot config
├── vercel.json             # Vercel routing rules
└── requirements.txt        # aiogram, yt-dlp, aiohttp, etc.
```

---

## 📋 Next Session Action Plan

1. **Traffic Launch**: Post TikTok/Reels showcasing watermark-free downloading with [@velo_save_bot](https://t.me/velo_save_bot).
2. **Sponsor Campaigns**: Add partner channels via `/add_sponsor` or the master CLI to monetize free download traffic.
