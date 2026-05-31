"""
AFK Plugin — v5 FINAL (All English)
Place at: HasiiMusic/plugins/features/afk.py

Commands:
  /afk [reason]   - Go AFK with GIF + styled message (auto-deletes in 1 min)
  /back           - Manually return from AFK
  /owner          - Show GROUP owner info + AFK status

GIF Management:
  /setafkgif, /rmafkgif <n>, /listafkgif
"""

import asyncio
import time
from datetime import timedelta

from pyrogram import enums, filters
from pyrogram.types import Message
from pymongo import MongoClient as PyMongoClient

from HasiiMusic.helpers.gif_manager import get_random_gif, register_gif_commands

try:
    from HasiiMusic.core.mongo import mongodb as _db
except Exception:
    import os
    _c = PyMongoClient(os.getenv("MONGO_DB_URI", "mongodb://localhost:27017"))
    _db = _c["HasiiMusicBot"]

from HasiiMusic import app

afk_col = _db["afk_users"]
AFK_DELETE_DELAY = 60


def _fmt_time(seconds: int) -> str:
    td = timedelta(seconds=max(0, int(seconds)))
    parts = []
    if td.days:
        parts.append(f"{td.days}d")
    h, r = divmod(td.seconds, 3600)
    m, s = divmod(r, 60)
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if not parts:
        parts.append(f"{s}s")
    return " ".join(parts)


async def _auto_delete(msg, delay: int = AFK_DELETE_DELAY):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


def is_afk(user_id: int):
    try:
        return afk_col.find_one({"user_id": user_id})
    except Exception:
        return None


def set_afk(user_id: int, reason: str):
    afk_col.update_one(
        {"user_id": user_id},
        {"$set": {"reason": reason, "since": int(time.time())}},
        upsert=True,
    )


def clear_afk(user_id: int):
    afk_col.delete_one({"user_id": user_id})


async def _send_afk_notify(client, chat_id, reply_to_msg, target, doc):
    duration = _fmt_time(int(time.time()) - doc["since"])
    reason = doc.get("reason", "No reason given.")

    full_msg = (
        f"<blockquote>"
        f"⚠️ <b>{target.first_name} is currently AFK!</b>\n\n"
        f"⏰ <b>Away for:</b> {duration}\n\n"
        f"<i>They will reply when they return 🌙</i>"
        f"</blockquote>\n"
        f"<blockquote>📝 <b>Reason:</b>\n{reason}</blockquote>"
    )

    gif = get_random_gif("afk")
    sent = None

    if gif:
        try:
            sent = await client.send_animation(
                chat_id, gif,
                caption=full_msg,
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            pass

    if not sent:
        try:
            if reply_to_msg:
                sent = await reply_to_msg.reply(full_msg, parse_mode=enums.ParseMode.HTML)
            else:
                sent = await client.send_message(chat_id, full_msg, parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass

    if sent:
        asyncio.create_task(_auto_delete(sent, AFK_DELETE_DELAY))


try:
    register_gif_commands(app, "afk", "afk")
except Exception:
    pass


@app.on_message(filters.command("afk") & (filters.group | filters.private))
async def afk_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return

    reason = " ".join(message.command[1:]).strip() if len(message.command) > 1 else "No reason given."
    set_afk(user.id, reason)

    full_msg = (
        f"<blockquote>"
        f"😴 <b>{user.first_name} is now AFK!</b>\n\n"
        f"╔══════════════════╗\n"
        f"║  💤  A F K  M O D E  💤  ║\n"
        f"╚══════════════════╝\n\n"
        f"👤 <b>User:</b> {user.mention}\n"
        f"⏰ <b>Since:</b> Just now\n\n"
        f"<i>Until they reply, consider them AFK 🌙</i>"
        f"</blockquote>\n"
        f"<blockquote>📝 <b>Reason:</b>\n{reason}</blockquote>"
    )

    gif = get_random_gif("afk")
    sent = None

    if gif:
        try:
            sent = await client.send_animation(
                message.chat.id, gif,
                caption=full_msg,
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            pass

    if not sent:
        try:
            sent = await message.reply(full_msg, parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass

    if sent:
        asyncio.create_task(_auto_delete(sent, AFK_DELETE_DELAY))

    try:
        await message.delete()
    except Exception:
        pass


@app.on_message(filters.command("back") & (filters.group | filters.private))
async def back_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return

    doc = is_afk(user.id)
    if not doc:
        return await message.reply(
            "<blockquote>ℹ️ You were not in AFK mode.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

    duration = _fmt_time(int(time.time()) - doc["since"])
    clear_afk(user.id)
    await message.reply(
        f"<blockquote>"
        f"✅ <b>Welcome back, {user.mention}!</b>\n\n"
        f"⏳ You were AFK for <b>{duration}</b>.\n"
        f"<i>Great to have you back! 🎉</i>"
        f"</blockquote>",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.group & ~filters.bot & ~filters.command(["afk", "back"]))
async def auto_back(client, message: Message):
    if not message.from_user:
        return

    doc = is_afk(message.from_user.id)
    if not doc:
        return

    duration = _fmt_time(int(time.time()) - doc["since"])
    clear_afk(message.from_user.id)

    try:
        sent = await message.reply(
            f"<blockquote>"
            f"✅ <b>Welcome back, {message.from_user.mention}!</b>\n\n"
            f"⏳ You were AFK for <b>{duration}</b>.\n"
            f"<i>Great to have you back! 🎉</i>"
            f"</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, AFK_DELETE_DELAY))
    except Exception:
        pass


@app.on_message(filters.group & ~filters.bot, group=10)
async def mention_check(client, message: Message):
    if not message.from_user:
        return

    targets = []

    if message.reply_to_message and message.reply_to_message.from_user:
        targets.append(message.reply_to_message.from_user)

    text = message.text or message.caption or ""
    entities = list(message.entities or []) + list(message.caption_entities or [])

    for ent in entities:
        try:
            etype = ent.type.value if hasattr(ent.type, "value") else str(ent.type)
        except Exception:
            continue

        if etype == "text_mention" and ent.user:
            targets.append(ent.user)
        elif etype == "mention" and text:
            uname = text[ent.offset + 1: ent.offset + ent.length]
            if uname:
                try:
                    u = await client.get_users(uname)
                    if u:
                        targets.append(u)
                except Exception:
                    pass

    seen_ids = set()
    for target in targets:
        if not target:
            continue
        if getattr(target, "is_bot", False):
            continue
        if target.id == message.from_user.id:
            continue
        if target.id in seen_ids:
            continue
        seen_ids.add(target.id)

        doc = is_afk(target.id)
        if not doc:
            continue

        await _send_afk_notify(client, message.chat.id, message, target, doc)


@app.on_message(filters.command("owner") & filters.group)
async def owner_cmd(client, message: Message):
    chat_name = getattr(message.chat, "title", None) or "This Group"

    owner = None
    try:
        async for member in client.get_chat_members(
            message.chat.id, filter=enums.ChatMembersFilter.OWNERS
        ):
            owner = member.user
            break
    except Exception:
        pass

    if not owner:
        try:
            async for member in client.get_chat_members(
                message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS
            ):
                if member.status == enums.ChatMemberStatus.OWNER:
                    owner = member.user
                    break
        except Exception:
            pass

    if not owner:
        return await message.reply(
            "<blockquote>❌ <b>Could not find the group owner!</b>\n\nMake sure the bot has admin rights.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

    owner_name = owner.first_name or "Owner"
    owner_username = f"@{owner.username}" if owner.username else "No username"
    owner_mention = owner.mention

    afk_doc = is_afk(owner.id)
    if afk_doc:
        duration = _fmt_time(int(time.time()) - afk_doc["since"])
        afk_status = f"💤 AFK since {duration} ago"
    else:
        afk_status = "✅ Online"

    text = (
        f"<blockquote>"
        f"👑 <b>Group Owner</b>\n\n"
        f"🏠 <b>Group:</b> {chat_name}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{owner_mention}\n\n"
        f"📛 <b>Name:</b> {owner_name}\n"
        f"🔗 <b>Username:</b> {owner_username}\n"
        f"🆔 <b>ID:</b> <code>{owner.id}</code>\n"
        f"📶 <b>Status:</b> {afk_status}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>Treat the group owner with respect! 👑</i>"
        f"</blockquote>"
    )
    await message.reply(text, parse_mode=enums.ParseMode.HTML)
