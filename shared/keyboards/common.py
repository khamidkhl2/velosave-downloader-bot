from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from shared.services.i18n_base import t

def get_main_reply_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Returns the persistent bottom reply keyboard."""
    kb = [
        [
            KeyboardButton(text=t("btn_vip", lang=lang)),
            KeyboardButton(text=t("btn_bots", lang=lang))
        ],
        [
            KeyboardButton(text=t("btn_referral", lang=lang)),
            KeyboardButton(text=t("btn_lang", lang=lang)),
            KeyboardButton(text=t("btn_help", lang=lang))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_language_inline_keyboard() -> InlineKeyboardMarkup:
    """Returns the 4-language switcher keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang:ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang:en")
        ],
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_lang:uz"),
            InlineKeyboardButton(text="🇪🇸 Español", callback_data="set_lang:es")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_sponsor_inline_keyboard(sponsors: List[Dict[str, Any]], lang: str = "en") -> InlineKeyboardMarkup:
    """Returns subscription buttons for unjoined sponsor channels and a check button."""
    buttons = []
    for idx, sp in enumerate(sponsors, 1):
        btn_text = t("sponsor_btn_subscribe", lang=lang, num=idx)
        buttons.append([InlineKeyboardButton(text=f"{btn_text}: {sp['title']}", url=sp["invite_link"])])

    buttons.append([InlineKeyboardButton(text=t("sponsor_btn_check", lang=lang), callback_data="check_sponsors")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_vip_inline_keyboard(stars: int, lang: str = "en") -> InlineKeyboardMarkup:
    """Returns the Stars checkout button and referral button."""
    buttons = [
        [InlineKeyboardButton(text=t("vip_btn_buy", lang=lang, stars=stars), callback_data="buy_vip_stars")],
        [InlineKeyboardButton(text=t("btn_referral", lang=lang), callback_data="view_referral")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_media_action_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Returns monetization and cross-promo buttons attached beneath downloaded media."""
    from shared.config_base import shared_config
    cpa_text = shared_config.get_cpa_button_text(lang)
    cpa_url = shared_config.CPA_BUTTON_URL
    buttons = [
        [InlineKeyboardButton(text=cpa_text, url=cpa_url)],
        [
            InlineKeyboardButton(text=t("btn_vip", lang=lang), callback_data="buy_vip_stars"),
            InlineKeyboardButton(text=t("btn_bots", lang=lang), callback_data="open_bots_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

