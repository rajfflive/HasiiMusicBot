"""
AFK Plugin — v4 FINAL
Place at: HasiiMusic/plugins/features/afk.py
"""

import asyncio
import time
from datetime import timedelta

from pyrogram import enums, filters
from pyrogram.types import Message

from HasiiMusic import app
from HasiiMusic.helpers.gif_manager import get_random_gif

_afk_users: dict[int, dict] = {}
_DEL = 86400


def _mention(user) -> str:
    name = (user.first_name or "User").replace("<", "&lt;").replace(">", "&gt;")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"


def _elapsed(since: float) -> str:
    secs = int(time.time() - since)
    delta = timedelta(seconds=secs)
    h, rem = divmod(delta.seconds, 3600)
    m, _ = divmod(rem, 60)
    parts = []
    if delta.days: parts.append(f"{delta.days}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    return " ".join(parts) if parts else "just now"


async def _del(msg, delay=_DEL):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


@app.on_message(filters.command("afk") & filters.group)
async def cmd_afk(_, message: Message):
    user = message.from_user
    if not user:
        return
    reason = " ".join(message.command[1:]).strip() or "No reason given"
    _afk_users[user.id] = {"reason": reason, "since": time.time(), "chat_id": message.chat.id}
    gif = get_random_gif("afk")
    text = (
        f"<blockquote>😴 <b>{_mention(user)} is now AFK!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Reason:</b> {reason}\n"
        f"⏰ <b>Since:</b> just now</blockquote>"
    )
    try:
        sent = await message.reply_animation(gif, caption=text, parse_mode=enums.ParseMode.HTML) if gif else await message.reply(text, parse_mode=enums.ParseMode.HTML)
    except Exception:
        sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_del(sent))
    try:
        await message.delete()
    except Exception:
        pass


@app.on_message(filters.command("afkoff") & filters.group)
async def cmd_afkoff(_, message: Message):
    user = message.from_user
    if not user:
        return
    if user.id not in _afk_users:
        s = await message.reply("<blockquote>ℹ️ You are not AFK right now.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 20))
        return
    data = _afk_users.pop(user.id)
    text = (
        f"<blockquote>✅ <b>{_mention(user)} is back!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Was AFK for:</b> {_elapsed(data['since'])}\n"
        f"📝 <b>Reason was:</b> {data['reason']}</blockquote>"
    )
    sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_del(sent))
    try:
        await message.delete()
    except Exception:
        pass


@app.on_message(filters.command("afklist") & filters.group)
async def cmd_afklist(_, message: Message):
    if not _afk_users:
        s = await message.reply("<blockquote>✅ No one is AFK right now!</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 20))
        return
    lines = [f"😴 <b>AFK Members ({len(_afk_users)})</b>\n━━━━━━━━━━━━━━━━━━"]
    for uid, data in _afk_users.items():
        lines.append(f"• <a href='tg://user?id={uid}'>User</a> — {_elapsed(data['since'])} ago\n  📝 {data['reason']}")
    sent = await message.reply("<blockquote>" + "\n".join(lines) + "</blockquote>", parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_del(sent))


@app.on_message(filters.command("owner") & filters.group)
async def cmd_owner(_, message: Message):
    chat_id = message.chat.id
    owner_user = None
    try:
        async for member in app.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if member.status == enums.ChatMemberStatus.OWNER and member.user:
                owner_user = member.user
                break
    except Exception as e:
        s = await message.reply(f"<blockquote>❌ Failed!\nMake sure I'm admin.\n<code>{e}</code></blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 20))
        return
    if not owner_user:
        s = await message.reply("<blockquote>⚠️ Could not find group owner.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 20))
        return
    name = (owner_user.first_name or "Owner").replace("<", "&lt;").replace(">", "&gt;")
    username = f"@{owner_user.username}" if owner_user.username else "No username"
    chat_name = (message.chat.title or "Group").replace("<", "&lt;").replace(">", "&gt;")
    text = (
        f"<blockquote>👑 <b>Group Owner</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏠 <b>Group:</b> {chat_name}\n"
        f"👤 <b>Owner:</b> <a href='tg://user?id={owner_user.id}'>{name}</a>\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{owner_user.id}</code></blockquote>"
    )
    sent = await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    asyncio.create_task(_del(sent))


@app.on_message(filters.group & filters.text & ~filters.bot)
async def afk_watcher(_, message: Message):
    try:
        if not message.from_user:
            return
        sender_id = message.from_user.id

        if sender_id in _afk_users:
            data = _afk_users.pop(sender_id)
            text = (
                f"<blockquote>✅ <b>{_mention(message.from_user)} is back!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⏱ <b>Was AFK for:</b> {_elapsed(data['since'])}\n"
                f"📝 <b>Reason was:</b> {data['reason']}</blockquote>"
            )
            sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
            asyncio.create_task(_del(sent))
            return

        mentioned_ids: list[int] = []
        if message.entities:
            for ent in message.entities:
                if ent.type == enums.MessageEntityType.TEXT_MENTION and ent.user:
                    mentioned_ids.append(ent.user.id)
                elif ent.type == enums.MessageEntityType.MENTION:
                    try:
                        uname = message.text[ent.offset + 1: ent.offset + ent.length]
                        u = await app.get_users(uname)
                        mentioned_ids.append(u.id)
                    except Exception:
                        pass  # PeerIdInvalid — skip silently

        if message.reply_to_message and message.reply_to_message.from_user:
            mentioned_ids.append(message.reply_to_message.from_user.id)

        for uid in set(mentioned_ids):
            if uid not in _afk_users:
                continue
            data = _afk_users[uid]
            gif = get_random_gif("afk")
            try:
                u = await app.get_users(uid)
                display = _mention(u)
            except Exception:
                display = f"<a href='tg://user?id={uid}'>This user</a>"
            text = (
                f"<blockquote>😴 <b>{display} is currently AFK!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📝 <b>Reason:</b> {data['reason']}\n"
                f"⏱ <b>AFK since:</b> {_elapsed(data['since'])} ago</blockquote>"
            )
            try:
                sent = await message.reply_animation(gif, caption=text, parse_mode=enums.ParseMode.HTML) if gif else await message.reply(text, parse_mode=enums.ParseMode.HTML)
            except Exception:
                sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
            asyncio.create_task(_del(sent))
    except Exception:
        pass  # Never crash on any message
