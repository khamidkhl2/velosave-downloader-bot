import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

# Ensure parent directory (tg_bots) is in sys.path for shared imports
BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from shared.config_base import shared_config

load_dotenv()

@dataclass
class DownloaderConfig:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", os.getenv("BOT_TOKEN_DOWNLOADER", ""))
    ADMIN_IDS: List[int] = None

    # Stars pricing & referrals
    VIP_PRICE_STARS: int = int(os.getenv("VIP_PRICE_STARS", str(shared_config.VIP_PRICE_STARS)))
    REFERRALS_FOR_VIP: int = int(os.getenv("REFERRALS_FOR_VIP", str(shared_config.REFERRALS_FOR_VIP)))

    # Download settings
    TEMP_DIR: str = os.getenv("TEMP_DIR", str(BASE_DIR / "temp"))
    MAX_FILESIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB Telegram limit
    MAX_VIDEO_HEIGHT: int = int(os.getenv("MAX_VIDEO_HEIGHT", "1080"))

    def __post_init__(self):
        admin_str = os.getenv("ADMIN_IDS", "")
        if admin_str:
            self.ADMIN_IDS = [int(x.strip()) for x in admin_str.split(",") if x.strip().isdigit()]
        else:
            self.ADMIN_IDS = shared_config.ADMIN_IDS
        os.makedirs(self.TEMP_DIR, exist_ok=True)

config = DownloaderConfig()
