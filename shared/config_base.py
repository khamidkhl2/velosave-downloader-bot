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
    FALLBACK_AD_TEXT: str = os.getenv("FALLBACK_AD_TEXT", "📢 Boost your Telegram channel with real active subscribers! Tap here")
    FALLBACK_AD_URL: str = os.getenv("FALLBACK_AD_URL", "https://t.me/CryptoBot")

    # CPA / Affiliate Partner Button (Configurable in .env)
    CPA_BUTTON_TEXT_EN: str = os.getenv("CPA_BUTTON_TEXT_EN", "🛡 High-Speed & Secure VPN (70% Off)")
    CPA_BUTTON_TEXT_RU: str = os.getenv("CPA_BUTTON_TEXT_RU", "🛡 Скоростной VPN (Скидка 70%)")
    CPA_BUTTON_TEXT_UZ: str = os.getenv("CPA_BUTTON_TEXT_UZ", "🛡 Tezkor va Xavfsiz VPN (-70%)")
    CPA_BUTTON_TEXT_ES: str = os.getenv("CPA_BUTTON_TEXT_ES", "🛡 VPN Rápida y Segura (-70%)")
    CPA_BUTTON_URL: str = os.getenv("CPA_BUTTON_URL", "https://t.me/CryptoBot")

    def get_cpa_button_text(self, lang: str = "en") -> str:
        lang = (lang or "en").lower()
        if lang == "ru":
            return self.CPA_BUTTON_TEXT_RU
        elif lang == "uz":
            return self.CPA_BUTTON_TEXT_UZ
        elif lang == "es":
            return self.CPA_BUTTON_TEXT_ES
        return self.CPA_BUTTON_TEXT_EN

    def __post_init__(self):
        admin_str = os.getenv("ADMIN_IDS", "5831301324")
        self.ADMIN_IDS = [int(x.strip()) for x in admin_str.split(",") if x.strip().isdigit()]

shared_config = SharedConfig()
