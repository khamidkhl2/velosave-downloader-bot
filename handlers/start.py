from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from shared.database.adapter import db
from shared.services.i18n_base import t
from shared.services.cross_promo import cross_promo
from shared.keyboards.common import (
    get_main_reply_keyboard,
    get_language_inline_keyboard,
    get_vip_inline_keyboard
)
from config import config

router = Router()

HELP_BUTTONS = {"❓ Help & Guide", "❓ Помощь", "❓ Yordam", "❓ Ayuda"}
BOTS_BUTTONS = {"⚡️ More Free Bots", "⚡️ Другие бесплатные боты", "⚡️ Boshqa bepul botlar", "⚡️ Más Bots Gratis"}
LANG_BUTTONS = {"🌐 Language", "🌐 Язык / Language", "🌐 Til / Language", "🌐 Idioma / Language"}
REF_BUTTONS = {"👥 Invite Friends", "👥 Пригласить друзей", "👥 Do'stlarni taklif qilish", "👥 Invitar amigos"}
VIP_BUTTONS = {"👑 VIP Pass (Ad-Free)", "👑 VIP Доступ (Без рекламы)", "👑 VIP Obuna (Reklamasiz)", "👑 Pase VIP (Sin anuncios)"}

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "Friend"
    tg_lang = message.from_user.language_code or "en"

    args = message.text.split()[1] if len(message.text.split()) > 1 else ""
    referrer_id = None
    if args.startswith("ref_") and args[4:].isdigit():
        ref_candidate = int(args[4:])
        if ref_candidate != user_id:
            referrer_id = ref_candidate

    user = await db.get_or_create_user(
        user_id=user_id,
        username=username,
        first_name=first_name,
        tg_lang=tg_lang,
        referrer_id=referrer_id
    )
    lang = user.get("language", "en")

    welcome_text = t(
        "welcome",
        lang=lang,
        bot_name="SaveFlow",
        bot_desc=t("downloader_desc", lang=lang)
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_reply_keyboard(lang),
        parse_mode="HTML"
    )

@router.message(Command("help"))
@router.message(F.text.in_(HELP_BUTTONS))
async def cmd_help(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user.get("language", "en") if user else "en"

    help_text = t(
        "help",
        lang=lang,
        bot_name="SaveFlow",
        bot_help=t("downloader_help", lang=lang)
    )
    await message.answer(help_text, parse_mode="HTML")

@router.message(Command("bots"))
@router.message(F.text.in_(BOTS_BUTTONS))
async def cmd_bots(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user.get("language", "en") if user else "en"

    kb = cross_promo.get_bots_keyboard(current_bot_id="downloader", lang=lang)
    await message.answer(
        t("bots_menu_title", lang=lang),
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.message(Command("lang"))
@router.message(F.text.in_(LANG_BUTTONS))
async def cmd_lang(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user.get("language", "en") if user else "en"

    await message.answer(
        t("lang_select", lang=lang),
        reply_markup=get_language_inline_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("referral"))
@router.message(F.text.in_(REF_BUTTONS))
async def cmd_referral(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user.get("language", "en") if user else "en"
    bot_info = await message.bot.get_me()

    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    ref_count = user.get("referral_count", 0) if user else 0

    text = t(
        "referral_title",
        lang=lang,
        needed=config.REFERRALS_FOR_VIP,
        count=ref_count,
        link=ref_link
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("vip"))
@router.message(F.text.in_(VIP_BUTTONS))
async def cmd_vip(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user.get("language", "en") if user else "en"

    if user and user.get("is_vip"):
        await message.answer(
            "⭐ <b>You are already a VIP Member!</b>\nAll ads and sponsor requirements are disabled for you.",
            parse_mode="HTML"
        )
        return

    text = t("vip_title", lang=lang, stars=config.VIP_PRICE_STARS)
    kb = get_vip_inline_keyboard(stars=config.VIP_PRICE_STARS, lang=lang)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")
