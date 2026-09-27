import random
from typing import Dict, List, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from shared.config_base import shared_config
from shared.services.i18n_base import t

# Directory of sister bots
FLEET_REGISTRY = [
    {
        "id": "tts",
        "name": "Voxify Voice",
        "username_attr": "BOT_USERNAME_TTS",
        "btn_key": "bots_btn_tts",
        "action_en": "voice text with realistic AI speech",
        "action_ru": "озвучить текст реалистичным голосом",
        "action_uz": "matnni AI ovoz bilan o'qitish",
        "action_es": "convertir texto a voz con IA realista"
    },
    {
        "id": "downloader",
        "name": "VeloSave",
        "username_attr": "BOT_USERNAME_DOWNLOADER",
        "btn_key": "bots_btn_downloader",
        "action_en": "download reels & videos from TikTok or Insta",
        "action_ru": "скачивать видео из TikTok и Instagram",
        "action_uz": "TikTok va Instagramdan video yuklab olish",
        "action_es": "descargar vídeos de TikTok o Instagram"
    },
    {
        "id": "chat",
        "name": "LumiChat",
        "username_attr": "BOT_USERNAME_CHAT",
        "btn_key": "bots_btn_chat",
        "action_en": "ask questions, write essays or solve homework",
        "action_ru": "задавать любые вопросы, писать тексты или код",
        "action_uz": "savollarga javob olish yoki matn yozdirish",
        "action_es": "hacer preguntas, redactar o resolver tareas"
    },
    {
        "id": "image",
        "name": "PixelCraft",
        "username_attr": "BOT_USERNAME_IMAGE",
        "btn_key": "bots_btn_image",
        "action_en": "generate stunning AI images & avatars",
        "action_ru": "создавать крутые арты и аватары через ИИ",
        "action_uz": "chiroyli AI rasm va avatarlar yaratish",
        "action_es": "crear increíbles imágenes y avatares con IA"
    },
    {
        "id": "utility",
        "name": "QuickTools",
        "username_attr": "BOT_USERNAME_UTILITY",
        "btn_key": "bots_btn_utility",
        "action_en": "remove image backgrounds or compress video",
        "action_ru": "удалить фон с фото или сжать видео",
        "action_uz": "rasm fonini o'chirish yoki videoni qisqartirish",
        "action_es": "quitar fondos de imágenes o comprimir vídeo"
    }
]

class CrossPromoManager:
    @staticmethod
    def get_tip_footer(current_bot_id: str, lang: str = "en") -> str:
        """
        Returns a subtle, non-intrusive promotional tip for a sister bot.
        """
        candidates = [b for b in FLEET_REGISTRY if b["id"] != current_bot_id]
        if not candidates:
            return ""
        pick = random.choice(candidates)
        username = getattr(shared_config, pick["username_attr"], "")
        if not username:
            return ""
        
        action_text = pick.get(f"action_{lang}", pick["action_en"])
        return t("cross_tip", lang=lang, action=action_text, username=username)

    @staticmethod
    def get_bots_keyboard(current_bot_id: str, lang: str = "en") -> InlineKeyboardMarkup:
        """
        Returns an inline keyboard with direct links to all other active sister bots.
        """
        buttons = []
        for b in FLEET_REGISTRY:
            if b["id"] == current_bot_id:
                continue
            username = getattr(shared_config, b["username_attr"], "")
            if not username:
                continue
            label = t(b["btn_key"], lang=lang)
            buttons.append([InlineKeyboardButton(text=label, url=f"https://t.me/{username}?start=net_{current_bot_id}")])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

cross_promo = CrossPromoManager()
