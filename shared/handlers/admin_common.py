import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from shared.database.adapter import db
from shared.config_base import shared_config

logger = logging.getLogger(__name__)
admin_router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in shared_config.ADMIN_IDS

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return

    stats = await db.get_stats()
    text = (
        "👑 <b>Admin Control Panel</b>\n\n"
        f"👥 <b>Total Users:</b> {stats['total_users']}\n"
        f"⭐ <b>VIP Subscribers:</b> {stats['total_vips']}\n"
        f"📢 <b>Active Sponsors:</b> {stats['active_sponsors']}\n"
        f"🎯 <b>Delivered Subscribers:</b> {stats['delivered_subs']}\n"
        f"⚡️ <b>Actions Today:</b> {stats['today_actions']}\n\n"
        "<b>Available Commands:</b>\n"
        "• <code>/add_sponsor &lt;@channel&gt; &lt;link&gt; &lt;target_subs&gt; &lt;Title&gt;</code>\n"
        "• <code>/sponsors</code> — View & manage sponsor campaigns\n"
        "• <code>/broadcast &lt;HTML text&gt;</code> — Send announcement to all users\n"
        "• <code>/give_vip &lt;user_id&gt; [days]</code> — Grant VIP pass"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Manage Sponsors", callback_data="admin_view_sponsors"),
            InlineKeyboardButton(text="📊 Refresh Stats", callback_data="admin_refresh_stats")
        ]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@admin_router.callback_query(F.data == "admin_refresh_stats")
async def callback_admin_refresh_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    stats = await db.get_stats()
    text = (
        "👑 <b>Admin Control Panel</b> (Updated)\n\n"
        f"👥 <b>Total Users:</b> {stats['total_users']}\n"
        f"⭐ <b>VIP Subscribers:</b> {stats['total_vips']}\n"
        f"📢 <b>Active Sponsors:</b> {stats['active_sponsors']}\n"
        f"🎯 <b>Delivered Subscribers:</b> {stats['delivered_subs']}\n"
        f"⚡️ <b>Actions Today:</b> {stats['today_actions']}\n\n"
        "<b>Available Commands:</b>\n"
        "• <code>/add_sponsor &lt;@channel&gt; &lt;link&gt; &lt;target_subs&gt; &lt;Title&gt;</code>\n"
        "• <code>/sponsors</code> — View & manage sponsor campaigns\n"
        "• <code>/broadcast &lt;HTML text&gt;</code> — Send announcement to all users\n"
        "• <code>/give_vip &lt;user_id&gt; [days]</code> — Grant VIP pass"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Manage Sponsors", callback_data="admin_view_sponsors"),
            InlineKeyboardButton(text="📊 Refresh Stats", callback_data="admin_refresh_stats")
        ]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer("Stats updated!")

@admin_router.message(Command("add_sponsor"))
async def cmd_add_sponsor(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split(maxsplit=4)
    if len(parts) < 5:
        await message.answer(
            "⚠️ <b>Usage:</b>\n"
            "<code>/add_sponsor &lt;@channel_id&gt; &lt;invite_link&gt; &lt;target_subs&gt; &lt;Title&gt;</code>\n\n"
            "Example:\n<code>/add_sponsor @tech_channel https://t.me/tech_channel 1000 Tech News</code>",
            parse_mode="HTML"
        )
        return

    channel_id = parts[1]
    invite_link = parts[2]
    try:
        target_subs = int(parts[3])
    except ValueError:
        await message.answer("❌ Target subscribers must be a number (e.g. 1000).")
        return
    title = parts[4]

    sponsor_id = await db.add_sponsor(
        channel_id=channel_id,
        title=title,
        invite_link=invite_link,
        target_subs=target_subs,
        owner_id=message.from_user.id
    )

    await message.answer(
        f"✅ <b>Sponsor #{sponsor_id} Activated!</b>\n\n"
        f"📢 <b>Title:</b> {title}\n"
        f"🆔 <b>Channel:</b> {channel_id}\n"
        f"🔗 <b>Link:</b> {invite_link}\n"
        f"🎯 <b>Target:</b> {target_subs} subscribers\n\n"
        f"🛡 <i>All non-VIP users must now subscribe to this channel to use the bot until {target_subs} subscribers are fulfilled.</i>",
        parse_mode="HTML"
    )

@admin_router.message(Command("sponsors"))
@admin_router.callback_query(F.data == "admin_view_sponsors")
async def cmd_list_sponsors(event):
    user_id = event.from_user.id
    if not is_admin(user_id):
        return

    sponsors = await db.get_active_sponsors()
    msg = event.message if isinstance(event, CallbackQuery) else event

    if not sponsors:
        text = "ℹ️ <b>No active sponsor campaigns.</b>\n\nUse <code>/add_sponsor</code> to add one."
        if isinstance(event, CallbackQuery):
            await event.answer()
            await msg.answer(text, parse_mode="HTML")
        else:
            await msg.answer(text, parse_mode="HTML")
        return

    for s in sponsors:
        text = (
            f"📢 <b>{s['title']}</b> (ID: {s['id']})\n"
            f"Channel: <code>{s['channel_id']}</code>\n"
            f"Link: {s['invite_link']}\n"
            f"Progress: <b>{s['delivered_subs']} / {s['target_subs']}</b> subscribers"
        )
        del_kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🗑 Delete Sponsor", callback_data=f"del_sponsor:{s['id']}")
        ]])
        await msg.answer(text, reply_markup=del_kb, parse_mode="HTML")

    if isinstance(event, CallbackQuery):
        await event.answer()

@admin_router.callback_query(F.data.startswith("del_sponsor:"))
async def callback_delete_sponsor(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    sponsor_id = int(callback.data.split(":", 1)[1])
    await db.remove_sponsor(sponsor_id)
    await callback.message.edit_text("🗑 <b>Sponsor removed from active rotation.</b>", parse_mode="HTML")
    await callback.answer("Deleted!")

@admin_router.message(Command("give_vip"))
async def cmd_give_vip(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: <code>/give_vip &lt;user_id&gt; [days]</code>", parse_mode="HTML")
        return
    try:
        target_user = int(parts[1])
        days = int(parts[2]) if len(parts) > 2 else 30
        await db.set_user_vip(target_user, days=days)
        await message.answer(f"✅ Granted {days} days of VIP to user <code>{target_user}</code>!", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Error granting VIP: {e}")

@admin_router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return

    text_to_broadcast = message.text[len("/broadcast"):].strip()
    if not text_to_broadcast:
        await message.answer("Usage: <code>/broadcast &lt;HTML announcement message&gt;</code>", parse_mode="HTML")
        return

    status_msg = await message.answer("🚀 Starting fleet broadcast...")
    user_ids = await db.get_all_user_ids()
    sent = 0
    failed = 0

    for uid in user_ids:
        try:
            await message.bot.send_message(chat_id=uid, text=text_to_broadcast, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"• Successfully sent: <b>{sent}</b>\n"
        f"• Failed/Blocked: <b>{failed}</b>",
        parse_mode="HTML"
    )
