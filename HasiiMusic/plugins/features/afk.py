"""
AFK Plugin — v3 FINAL (All English)
Place at: HasiiMusic/plugins/features/afk.py

Commands:
  /afk [reason]   - Set yourself as AFK
  /afkoff         - Manually remove your AFK status (also auto-removed on any message)
  /afklist        - Show all currently AFK members in this group
  /owner          - Show group owner info

Note: When an AFK user is mentioned, the bot replies with an AFK gif (NOT couple gif).
Auto-unset: AFK removed when the AFK user sends any message.
"""

import asyncio
import time
from datetime import timedelta

from pyrogram import enums, filters, types
from pyrogram.types import Message

from HasiiMusic import app
from HasiiMusic.helpers.gif_manager import get_random_gif

# ── Storage ──────────────────────────────────────────────────────────────────
# { user_id: { "reason": str, "since": float, "chat_id": int } }
_afk_users: dict[int, dict] = {}

AFK_DELETE_DELAY = 86400  # 24 hours


# ── Helpers ──────────────────────────────────────────────────────────────────

def _mention(user) -> str:
    name = (user.first_name or "User").replace("<", "&lt;").replace(">", "&gt;")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"


def _elapsed(since: float) -> str:
    secs = int(time.time() - since)
    delta = timedelta(seconds=secs)
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if delta.days:
        parts.append(f"{delta.days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "just now"


async def _auto_delete(msg: Message, delay: int = AFK_DELETE_DELAY):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


# ── /afk ─────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("afk") & filters.group)
async def cmd_afk(_, message: Message):
    user = message.from_user
    if not user:
        return

    reason = " ".join(message.command[1:]).strip() or "No reason given"

    _afk_users[user.id] = {
        "reason": reason,
        "since": time.time(),
        "chat_id": message.chat.id,
    }

    gif = get_random_gif("afk")
    text = (
        f"<blockquote>"
        f"😴 <b>{_mention(user)} is now AFK!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Reason:</b> {reason}\n"
        f"⏰ <b>Since:</b> just now"
        f"</blockquote>"
    )

    try:
        if gif:
            sent = await message.reply_animation(
                gif,
                caption=text,
                parse_mode=enums.ParseMode.HTML,
            )
        else:
            sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
    except Exception:
        sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)

    asyncio.create_task(_auto_delete(sent, AFK_DELETE_DELAY))

    try:
        await message.delete()
    except Exception:
        pass


# ── /afkoff ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("afkoff") & filters.group)
async def cmd_afkoff(_, message: Message):
    user = message.from_user
    if not user:
        return

    if user.id not in _afk_users:
        sent = await message.reply(
            "<blockquote>ℹ️ You are not AFK right now.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 30))
        return

    data = _afk_users.pop(user.id)
    elapsed = _elapsed(data["since"])

    text = (
        f"<blockquote>"
        f"✅ <b>{_mention(user)} is back!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Was AFK for:</b> {elapsed}\n"
        f"📝 <b>Reason was:</b> {data['reason']}"
        f"</blockquote>"
    )
    sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_auto_delete(sent, AFK_DELETE_DELAY))

    try:
        await message.delete()
    except Exception:
        pass


# ── /afklist ──────────────────────────────────────────────────────────────────

@app.on_message(filters.command("afklist") & filters.group)
async def cmd_afklist(_, message: Message):
    if not _afk_users:
        sent = await message.reply(
            "<blockquote>✅ No one is AFK right now!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 30))
        return

    lines = [f"😴 <b>AFK Members ({len(_afk_users)})</b>\n━━━━━━━━━━━━━━━━━━"]
    for uid, data in _afk_users.items():
        elapsed = _elapsed(data["since"])
        lines.append(
            f"• <a href='tg://user?id={uid}'>User {uid}</a> — {elapsed} ago\n"
            f"  📝 {data['reason']}"
        )

    text = "<blockquote>" + "\n".join(lines) + "</blockquote>"
    sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_auto_delete(sent, AFK_DELETE_DELAY))


# ── /owner ────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("owner") & filters.group)
async def cmd_owner(_, message: Message):
    chat_id = message.chat.id

    # Find the group creator (OWNER status)
    owner_user = None
    try:
        async for member in app.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if member.status == enums.ChatMemberStatus.OWNER and member.user:
                owner_user = member.user
                break
    except Exception as e:
        sent = await message.reply(
            f"<blockquote>❌ <b>Failed to fetch group owner!</b>\n"
            f"Make sure I am an admin.\n<code>{e}</code></blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 30))
        return

    if not owner_user:
        sent = await message.reply(
            "<blockquote>⚠️ Could not find this group's owner.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 30))
        return

    name = (owner_user.first_name or "Owner").replace("<", "&lt;").replace(">", "&gt;")
    username = f"@{owner_user.username}" if owner_user.username else "No username"
    chat_name = (message.chat.title or "This Group").replace("<", "&lt;").replace(">", "&gt;")

    text = (
        f"<blockquote>"
        f"👑 <b>Group Owner</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏠 <b>Group:</b> {chat_name}\n"
        f"👤 <b>Owner:</b> <a href='tg://user?id={owner_user.id}'>{name}</a>\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{owner_user.id}</code>"
        f"</blockquote>"
    )

    sent = await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    asyncio.create_task(_auto_delete(sent, AFK_DELETE_DELAY))


# ── Auto-detect: AFK user mentioned ──────────────────────────────────────────

@app.on_message(filters.group & ~filters.bot)
async def afk_watcher(_, message: Message):
    if not message.from_user:
        return

    sender_id = message.from_user.id

    # ── Auto-unset if AFK user sends a message ────────────────────────────
    if sender_id in _afk_users:
        data = _afk_users.pop(sender_id)
        elapsed = _elapsed(data["since"])
        text = (
            f"<blockquote>"
            f"✅ <b>{_mention(message.from_user)} is back!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⏱ <b>Was AFK for:</b> {elapsed}\n"
            f"📝 <b>Reason was:</b> {data['reason']}"
            f"</blockquote>"
        )
        sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(sent, AFK_DELETE_DELAY))
        return  # Don't process mentions in the same message

    # ── Check if any mentioned user is AFK ───────────────────────────────
    mentioned_ids: list[int] = []

    # Collect from entities
    if message.entities:
        for ent in message.entities:
            if ent.type == enums.MessageEntityType.MENTION:
                username = message.text[ent.offset + 1: ent.offset + ent.length]
                try:
                    u = await app.get_users(username)
                    mentioned_ids.append(u.id)
                except Exception:
                    pass
            elif ent.type == enums.MessageEntityType.TEXT_MENTION and ent.user:
                mentioned_ids.append(ent.user.id)

    # Also check reply-to
    if message.reply_to_message and message.reply_to_message.from_user:
        mentioned_ids.append(message.reply_to_message.from_user.id)

    for uid in set(mentioned_ids):
        if uid in _afk_users:
            data = _afk_users[uid]
            elapsed = _elapsed(data["since"])

            gif = get_random_gif("afk")  # AFK gif, NOT couple gif

            try:
                u = await app.get_users(uid)
                display = _mention(u)
            except Exception:
                display = f"<a href='tg://user?id={uid}'>This user</a>"

            text = (
                f"<blockquote>"
                f"😴 <b>{display} is currently AFK!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📝 <b>Reason:</b> {data['reason']}\n"
                f"⏱ <b>AFK since:</b> {elapsed} ago"
                f"</blockquote>"
            )

            try:
                if gif:
                    sent = await message.reply_animation(
                        gif,
                        caption=text,
                        parse_mode=enums.ParseMode.HTML,
                    )
                else:
                    sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
            except Exception:
                sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)

            asyncio.create_task(_auto_delete(sent, AFK_DELETE_DELAY))
