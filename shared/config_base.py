import os
from dataclasses import dataclass, field
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SharedConfig:
    ADMIN_IDS: List[int] = field(default_factory=list)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "") # e.g. postgresql://user:pass@host:5432/dbname or empty for SQLite
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared_empire.db"))

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
    BOT_USERNAME_DOWNLOADER: str = os.getenv("BOT_USERNAME_DOWNLOADER", "SaveFlowBot")
    BOT_USERNAME_CHAT: str = os.getenv("BOT_USERNAME_CHAT", "NexaChatBot")
    BOT_USERNAME_IMAGE: str = os.getenv("BOT_USERNAME_IMAGE", "PixelCraftBot")
    BOT_USERNAME_UTILITY: str = os.getenv("BOT_USERNAME_UTILITY", "QuickToolsBot")

    # API Keys for AI
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Fallback ad link if no active sponsor is found
    FALLBACK_AD_TEXT: str = os.getenv("FALLBACK_AD_TEXT", "📢 Boost your Telegram channel with real active subscribers! Tap here")
    FALLBACK_AD_URL: str = os.getenv("FALLBACK_AD_URL", "https://t.me/CryptoBot")

    def __post_init__(self):
        admin_str = os.getenv("ADMIN_IDS", "5831301324")
        self.ADMIN_IDS = [int(x.strip()) for x in admin_str.split(",") if x.strip().isdigit()]

shared_config = SharedConfig()
