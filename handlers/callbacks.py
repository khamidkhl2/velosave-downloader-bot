import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery, LabeledPrice

from shared.database.adapter import db
from shared.services.i18n_base import t
from shared.services.sponsor_service import sponsor_service
from shared.keyboards.common import (
    get_main_reply_keyboard,
    get_sponsor_inline_keyboard
)
from config import config

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data.startswith("set_lang:"))
async def callback_set_lang(callback: CallbackQuery):
    lang_code = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    await db.set_user_language(user_id, lang_code)
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        t("lang_changed", lang=lang_code),
        reply_markup=get_main_reply_keyboard(lang=lang_code),
        parse_mode="HTML"
    )
    await callback.answer("✅")

@router.callback_query(F.data == "check_sponsors")
async def callback_check_sponsors(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    lang = user.get("language", "en") if user else "en"

    is_passed, missing = await sponsor_service.check_user_subscription(callback.bot, user_id)

    if is_passed:
        try:
            await callback.message.edit_text(
                t("sponsor_verified", lang=lang),
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.answer(t("sponsor_verified", lang=lang), parse_mode="HTML")
        await callback.answer("✅")
    else:
        kb = get_sponsor_inline_keyboard(missing, lang=lang)
        try:
            await callback.message.edit_text(
                t("sponsor_gate_title", lang=lang),
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception:
            pass
        await callback.answer(t("sponsor_not_subbed", lang=lang), show_alert=True)

@router.callback_query(F.data == "buy_vip_stars")
async def callback_buy_vip_stars(callback: CallbackQuery):
    user_id = callback.from_user.id
    prices = [LabeledPrice(label="VeloSave VIP Pass (30 Days)", amount=config.VIP_PRICE_STARS)]

    await callback.bot.send_invoice(
        chat_id=callback.message.chat.id,
        title="⭐ VeloSave 30-Day VIP Pass",
        description="Unlimited downloads, zero ads, bypass all sponsor requirements.",
        payload=f"vip_{user_id}",
        currency="XTR",
        prices=prices
    )
    await callback.answer()

@router.callback_query(F.data == "view_referral")
async def callback_view_referral(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user.get("language", "en") if user else "en"
    bot_info = await callback.bot.get_me()

    ref_link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"
    ref_count = user.get("referral_count", 0) if user else 0

    text = t(
        "referral_title",
        lang=lang,
        needed=config.REFERRALS_FOR_VIP,
        count=ref_count,
        link=ref_link
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    user = await db.get_user(message.from_user.id)
    lang = user.get("language", "en") if user else "en"

    if payload.startswith("vip_"):
        user_id = int(payload.split("_")[1])
        await db.set_user_vip(user_id, days=30)
        await message.answer(
            t("vip_success", lang=lang),
            parse_mode="HTML"
        )
