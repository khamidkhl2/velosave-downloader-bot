import sys
from pathlib import Path

# Ensure parent directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from config import config
from shared.database.adapter import db
from handlers.start import router as start_router
from handlers.callbacks import router as callbacks_router
from handlers.download import router as download_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("VeloSave")

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Start bot / Main menu"),
        BotCommand(command="help", description="How to download videos & photos"),
        BotCommand(command="bots", description="Discover our free bot network"),
        BotCommand(command="vip", description="Get VIP Pass (Ad-free)"),
        BotCommand(command="lang", description="Switch language"),
        BotCommand(command="referral", description="Invite friends for free VIP"),
    ]
    await bot.set_my_commands(commands)

async def main():
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN is not set in environment or .env file! Please set it.")
        return

    logger.info("Initializing shared database...")
    await db.init()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register Routers
    dp.include_router(callbacks_router)
    dp.include_router(start_router)
    # Download handler catches text URLs, must be after start/commands
    dp.include_router(download_router)

    await set_commands(bot)

    bot_user = await bot.get_me()
    logger.info(f"VeloSave Downloader Bot @{bot_user.username} is successfully running!")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
