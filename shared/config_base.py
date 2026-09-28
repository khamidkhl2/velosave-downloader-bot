import os
from dataclasses import dataclass, field
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SharedConfig:
    ADMIN_IDS: List[int] = field(default_factory=list)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "") # e.g. postgresql://user:pass@host:5432/dbname or empty for SQLite
    DEFAULT_SQLITE: str = "/tmp/shared_empire.db" if os.getenv("VERCEL") else os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared_empire.db")
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", DEFAULT_SQLITE)

    # Monetization
    CRYPTO_PAY_TOKEN: str = os.getenv("CRYPTO_PAY_TOKEN", "")
    CRYPTO_PAY_NET: str = os.getenv("CRYPTO_PAY_NET", "mainnet") # mainnet or testnet
    VIP_PRICE_STARS: int = int(os.getenv("VIP_PRICE_STARS", "50"))
    REFERRALS_FOR_VIP: int = int(os.getenv("REFERRALS_FOR_VIP", "3"))

    # Free daily quotas per bot
    DAILY_LIMIT_CHAT: int = int(os.getenv("DAILY_LIMIT_CHAT", "15"))
    DAILY_LIMIT_IMAGE: int = int(os.getenv("DAILY_LIMIT_IMAGE", "5"))
    DAILY_LIMIT_UTILITY: int = int(os.getenv("DAILY_LIMIT_UTILITY", "5"))

    # Sister Bot Usernames for Cross-Promotion (customizable in .env)
    BOT_USERNAME_TTS: str = os.getenv("BOT_USERNAME_TTS", "VoxifyVoiceBot")
    BOT_USERNAME_DOWNLOADER: str = os.getenv("BOT_USERNAME_DOWNLOADER", "velo_save_bot")
    BOT_USERNAME_CHAT: str = os.getenv("BOT_USERNAME_CHAT", "lumichat_ai_bot")
    BOT_USERNAME_IMAGE: str = os.getenv("BOT_USERNAME_IMAGE", "")
    BOT_USERNAME_UTILITY: str = os.getenv("BOT_USERNAME_UTILITY", "")

    # API Keys for AI
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Fallback ad link if no active sponsor is found
    FALLBACK_AD_TEXT: str = os.getenv("FALLBACK_AD_TEXT", "📢 Boost your Telegram channel with real active subscribers! Contact @khamidkhl")
    FALLBACK_AD_URL: str = os.getenv("FALLBACK_AD_URL", "https://t.me/khamidkhl")

    # Administrator Telegram Username (for direct sponsor sales & inquiries)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "khamidkhl")

    # Static / Persistent Sponsor Gate (env fallback for serverless)
    STATIC_SPONSOR_CHANNEL: str = os.getenv("STATIC_SPONSOR_CHANNEL", "")
    STATIC_SPONSOR_LINK: str = os.getenv("STATIC_SPONSOR_LINK", "")
    STATIC_SPONSOR_TITLE: str = os.getenv("STATIC_SPONSOR_TITLE", "Partner Channel")
    STATIC_SPONSOR_TARGET: int = int(os.getenv("STATIC_SPONSOR_TARGET", "1000"))

    # CPA / Sponsor Promotion Button
    CPA_BUTTON_TEXT_EN: str = os.getenv("CPA_BUTTON_TEXT_EN", "📢 Promote Channel (Buy 1k-10k Subs)")
    CPA_BUTTON_TEXT_RU: str = os.getenv("CPA_BUTTON_TEXT_RU", "📢 Реклама канала (Купить 1к-10к пдп)")
    CPA_BUTTON_TEXT_UZ: str = os.getenv("CPA_BUTTON_TEXT_UZ", "📢 Kanalni reklama qilish (1k-10k obunachi)")
    CPA_BUTTON_TEXT_ES: str = os.getenv("CPA_BUTTON_TEXT_ES", "📢 Anunciar canal (1k-10k subs)")
    CPA_BUTTON_URL: str = os.getenv("CPA_BUTTON_URL", "https://t.me/khamidkhl")

    def get_cpa_button_text(self, lang: str = "en") -> str:
        lang = (lang or "en").lower()
        if lang == "ru":
            return self.CPA_BUTTON_TEXT_RU
        elif lang == "uz":
            return self.CPA_BUTTON_TEXT_UZ
        elif lang == "es":
            return self.CPA_BUTTON_TEXT_ES
        return self.CPA_BUTTON_TEXT_EN

    def get_cpa_button_url(self, lang: str = "en") -> str:
        lang = (lang or "en").lower()
        if lang == "ru":
            return f"https://t.me/{self.ADMIN_USERNAME}?text=%D0%97%D0%B4%D1%80%D0%B0%D0%B2%D1%81%D1%82%D0%B2%D1%83%D0%B9%D1%82%D0%B5!%20%D0%A5%D0%BE%D1%87%D1%83%20%D0%B7%D0%B0%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D1%8C%20%D1%80%D0%B5%D0%BA%D0%BB%D0%B0%D0%BC%D1%83%2F%D1%81%D0%BF%D0%BE%D0%BD%D1%81%D0%BE%D1%80%D1%81%D1%82%D0%B2%D0%BE%20%D0%B2%20%D1%81%D0%B5%D1%82%D0%B8%20%D0%B1%D0%BE%D1%82%D0%BE%D0%B2"
        elif lang == "uz":
            return f"https://t.me/{self.ADMIN_USERNAME}?text=Assalomu%20alaykum!%20Botlar%20tarmog%27ida%20kanalimni%20reklama%20qilmoqchiman"
        elif lang == "es":
            return f"https://t.me/{self.ADMIN_USERNAME}?text=%C2%A1Hola!%20Quiero%20comprar%20publicidad%20en%20su%20red%20de%20bots"
        return f"https://t.me/{self.ADMIN_USERNAME}?text=Hello!%20I%20want%20to%20order%20sponsorship%2Fadvertising%20in%20your%20bot%20network"

    def __post_init__(self):
        admin_str = os.getenv("ADMIN_IDS", "5831301324")
        self.ADMIN_IDS = [int(x.strip()) for x in admin_str.split(",") if x.strip().isdigit()]

shared_config = SharedConfig()
