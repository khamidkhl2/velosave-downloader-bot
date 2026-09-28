import os
import sys
import json
import asyncio
import traceback
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Ensure paths are set for Vercel
CURRENT_DIR = Path(__file__).resolve().parent.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

_dp = None

def create_bot():
    from aiogram import Bot
    from aiogram.enums import ParseMode
    from aiogram.client.default import DefaultBotProperties
    from config import config

    token = config.BOT_TOKEN or os.getenv("BOT_TOKEN", "")
    if not token:
        raise ValueError("BOT_TOKEN is missing! Please configure it in Vercel Environment Variables.")
    return Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

def get_dispatcher():
    global _dp
    if _dp is None:
        from aiogram import Dispatcher
        from handlers.callbacks import router as callbacks_router
        from handlers.start import router as start_router
        from handlers.download import router as download_router
        from shared.handlers.admin_common import admin_router

        _dp = Dispatcher()
        _dp.include_router(admin_router)
        _dp.include_router(callbacks_router)
        _dp.include_router(start_router)
        _dp.include_router(download_router)
    return _dp

async def process_update(data: dict):
    from aiogram.types import Update
    from shared.database.adapter import db

    await db.init()
    bot = create_bot()
    try:
        dp = get_dispatcher()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot=bot, update=update)
    finally:
        await bot.session.close()

async def configure_webhook(webhook_url: str):
    bot = create_bot()
    try:
        dp = get_dispatcher()
        allowed_updates = dp.resolve_used_update_types()
        res = await bot.set_webhook(url=webhook_url, allowed_updates=allowed_updates)
        info = await bot.get_webhook_info()
        return res, info
    finally:
        await bot.session.close()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from config import config
            host = self.headers.get("Host", "")
            path = self.path

            if "set_webhook" in path:
                webhook_url = f"https://{host}/"
                res, info = asyncio.run(configure_webhook(webhook_url))
                msg = (
                    f"<h1>✅ VeloSave Webhook Configured!</h1>"
                    f"<p><b>Target URL:</b> {webhook_url}</p>"
                    f"<p><b>Telegram Webhook URL:</b> {info.url}</p>"
                    f"<p><b>Pending Updates:</b> {info.pending_update_count}</p>"
                    f"<p>👉 Open Telegram and test @velo_save_bot!</p>"
                )
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(msg.encode("utf-8"))
                return

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            token_status = "Configured ✅" if (os.getenv("BOT_TOKEN") or config.BOT_TOKEN) else "Missing ❌"
            html = (
                f"<h2>📥 VeloSave Downloader Bot is Live on Vercel!</h2>"
                f"<p><b>BOT_TOKEN Status:</b> {token_status}</p>"
                f"<p><a href='/set_webhook' style='padding: 8px 16px; background: #0070f3; color: white; text-decoration: none; border-radius: 5px;'>Click Here to Connect Telegram Webhook</a></p>"
            )
            self.wfile.write(html.encode("utf-8"))

        except Exception as e:
            tb = traceback.format_exc()
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            err_msg = f"⚠️ VeloSave Serverless Error:\n\n{tb}"
            self.wfile.write(err_msg.encode("utf-8"))

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            if not body:
                self.send_response(200)
                self.end_headers()
                return

            data = json.loads(body.decode("utf-8"))
            asyncio.run(process_update(data))

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Error handling webhook: {tb}")
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            err_dict = {"ok": False, "error": str(e), "traceback": tb}
            self.wfile.write(json.dumps(err_dict).encode("utf-8"))
