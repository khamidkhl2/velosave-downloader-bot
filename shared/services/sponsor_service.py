import logging
from typing import Tuple, List, Dict, Any
from aiogram import Bot
from aiogram.enums import ChatMemberStatus

from shared.database.adapter import db

logger = logging.getLogger(__name__)

VALID_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.CREATOR
}

class SponsorService:
    @staticmethod
    async def check_user_subscription(bot: Bot, user_id: int) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Verifies if the user is VIP or is subscribed to all active sponsor channels.
        Returns: (is_fully_subscribed, list_of_missing_sponsors)
        """
        user = await db.get_user(user_id)
        if user and user.get("is_vip"):
            return True, []

        active_sponsors = await db.get_active_sponsors()
        if not active_sponsors:
            return True, []

        missing_sponsors = []
        for sponsor in active_sponsors:
            channel_id = sponsor["channel_id"]
            try:
                # Can be -100... or @channel_username
                member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if member.status not in VALID_STATUSES:
                    missing_sponsors.append(sponsor)
                else:
                    # User is subscribed, register delivery credit in DB
                    await db.record_sponsor_delivery(user_id, sponsor["id"])
            except Exception as e:
                logger.warning(f"Error checking member {user_id} in channel {channel_id}: {e}")
                # If bot is not admin or channel is unreachable, do not block user
                continue

        return (len(missing_sponsors) == 0), missing_sponsors

sponsor_service = SponsorService()
