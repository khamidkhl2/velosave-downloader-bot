import re
import html
import logging
from aiogram import Router, F
from aiogram.types import Message, FSInputFile

from shared.database.adapter import db
from shared.services.i18n_base import t
from shared.services.sponsor_service import sponsor_service
from shared.services.cross_promo import cross_promo
from shared.keyboards.common import get_sponsor_inline_keyboard
from services.downloader import downloader_service, FileSizeExceededError, MediaDownloadError

logger = logging.getLogger(__name__)
router = Router()

URL_REGEX = re.compile(r'https?://[^\s]+')

@router.message(F.text.regexp(URL_REGEX))
async def handle_url_message(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        user = await db.get_or_create_user(
            user_id=user_id,
            username=message.from_user.username or "",
            first_name=message.from_user.first_name or "",
            tg_lang=message.from_user.language_code or "en"
        )
    lang = user.get("language", "en")

    # 1. Sponsor Gating Check
    is_subbed, missing = await sponsor_service.check_user_subscription(message.bot, user_id)
    if not is_subbed:
        kb = get_sponsor_inline_keyboard(missing, lang=lang)
        await message.answer(
            t("sponsor_gate_title", lang=lang),
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    # 2. Extract URL
    match = URL_REGEX.search(message.text)
    if not match:
        await message.answer(t("dl_invalid_url", lang=lang), parse_mode="HTML")
        return

    url = match.group(0)

    # 3. Status Notification
    status_msg = await message.answer(t("dl_processing", lang=lang), parse_mode="HTML")

    # 4. Download and Send
    download_res = None
    try:
        download_res = await downloader_service.download(url)

        for item in download_res.items:
            size_mb = item.size_bytes / (1024 * 1024)
            if size_mb > 50.0:
                await message.answer(
                    t("dl_file_too_large", lang=lang, size_mb=size_mb),
                    parse_mode="HTML"
                )
                continue

            # Clean caption with no author nicknames or titles
            caption = "📥 <b>Downloaded via @velo_save_bot</b>"

            if item.media_type == "video":
                await message.answer_video(
                    video=FSInputFile(item.file_path),
                    caption=caption,
                    parse_mode="HTML",
                    supports_streaming=True,
                    duration=item.duration,
                    width=item.width,
                    height=item.height
                )
            elif item.media_type == "photo":
                await message.answer_photo(
                    photo=FSInputFile(item.file_path),
                    caption=caption,
                    parse_mode="HTML"
                )
            elif item.media_type == "audio":
                await message.answer_audio(
                    audio=FSInputFile(item.file_path),
                    caption=caption,
                    parse_mode="HTML"
                )

        try:
            await status_msg.delete()
        except Exception:
            pass

        # Track usage and send separate promotional tip 1 in 2 videos (every other video)
        dl_count = await db.increment_daily_usage(user_id, "downloader")
        if dl_count % 2 == 0:
            seq_idx = (dl_count // 2) - 1
            tip_msg = cross_promo.get_alternating_tip("downloader", sequence_index=seq_idx, lang=lang)
            if tip_msg:
                await message.answer(tip_msg, parse_mode="HTML")

    except FileSizeExceededError as e:
        logger.warning(f"File size exceeded for {url}: {e.size_mb:.1f} MB")
        try:
            await status_msg.delete()
        except Exception:
            pass
        await message.answer(
            t("dl_file_too_large", lang=lang, size_mb=e.size_mb),
            parse_mode="HTML"
        )
    except MediaDownloadError as e:
        logger.warning(f"Download failed for {url}: {e}")
        try:
            await status_msg.delete()
        except Exception:
            pass
        await message.answer(t("dl_unsupported", lang=lang), parse_mode="HTML")
    except Exception as e:
        logger.exception(f"Unexpected error downloading {url}: {e}")
        try:
            await status_msg.delete()
        except Exception:
            pass
        await message.answer(t("dl_unsupported", lang=lang), parse_mode="HTML")
    finally:
        if download_res:
            download_res.cleanup()

@router.message(F.text)
async def handle_non_url_text(message: Message):
    """Fallback handler for arbitrary text messages without URL."""
    user = await db.get_user(message.from_user.id)
    lang = user.get("language", "en") if user else "en"
    await message.answer(t("dl_invalid_url", lang=lang), parse_mode="HTML")
