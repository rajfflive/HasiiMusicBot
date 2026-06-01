"""
Welcome Plugin — v5 PREMIUM
Place at: HasiiMusic/plugins/features/welcome.py

Commands (admin only):
  /setwel <text>  - Set custom welcome
  /wel            - Preview welcome
  /welon          - Enable welcome
  /weloff         - Disable welcome

Placeholders: {mention} {first} {username} {count} {chat}
"""

import asyncio
import random

from pyrogram import enums, filters
from pyrogram.types import Message

from HasiiMusic import app
from HasiiMusic.helpers.gif_manager import get_random_gif

_cfg: dict[int, dict] = {}

WELCOME_QUOTES = [
    "Every expert was once a beginner. Welcome aboard! 🚀",
    "New member, new energy! Glad to have you. ✨",
    "The more the merrier! Welcome to the family. 🎊",
    "Great minds think alike — and you just joined them. 💡",
    "Your journey with us starts now. Make it legendary! 🏆",
    "We were good before. Now with you, we're even better! 🌟",
    "A new chapter begins. Welcome, and enjoy the ride! 🎯",
]

BADGES = ["🌟", "💎", "🔥", "⭐", "🎯", "👑", "🏆", "🦋"]


def _get(chat_id: int) -> dict:
    if chat_id not in _cfg:
        _cfg[chat_id] = {"text": None, "on": True}
    return _cfg[chat_id]


def _fmt(template: str, user, chat, count: int) -> str:
    first = (user.first_name or "").replace("<", "&lt;").replace(">", "&gt;")
    username = f"@{user.username}" if user.username else first
    chat_name = (chat.title or "Group").replace("<", "&lt;").replace(">", "&gt;")
    mention = f"<a href='tg://user?id={user.id}'>{first}</a>"
    return (
        template
        .replace("{mention}", mention)
        .replace("{first}", first)
        .replace("{username}", username)
        .replace("{count}", str(count))
        .replace("{chat}", chat_name)
    )


def _build_welcome(user, chat, count: int) -> str:
    first = (user.first_name or "Friend").replace("<", "&lt;").replace(">", "&gt;")
    mention = f"<a href='tg://user?id={user.id}'>{first}</a>"
    chat_name = (chat.title or "our group").replace("<", "&lt;").replace(">", "&gt;")
    return (
        f"<blockquote>"
        f"┌──────────────────────\n"
        f"│  {random.choice(BADGES)}  WELCOME!\n"
        f"└──────────────────────\n"
        f"\n"
        f"👋 Hey {mention}!\n"
        f"You just joined <b>{chat_name}</b> ✨\n"
        f"\n"
        f"─────────────────────\n"
        f"🎊 <b>Member Count:</b> #{count}\n"
        f"─────────────────────\n"
        f"\n"
        f"💬 <i>{random.choice(WELCOME_QUOTES)}</i>\n"
        f"\n"
        f"📌 Read the group rules.\n"
        f"🤝 Be respectful & have fun!"
        f"</blockquote>"
    )


async def _is_admin(chat_id, user_id) -> bool:
    try:
        m = await app.get_chat_member(chat_id, user_id)
        return m.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)
    except Exception:
        return False


async def _del(msg, delay=60):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


@app.on_message(filters.new_chat_members & filters.group)
async def on_join(_, message: Message):
    chat_id = message.chat.id
    cfg = _get(chat_id)
    if not cfg["on"]:
        return
    for user in message.new_chat_members:
        if user.is_bot:
            continue
        try:
            count = await app.get_chat_members_count(chat_id)
        except Exception:
            count = 0
        text = "<blockquote>" + _fmt(cfg["text"], user, message.chat, count) + "</blockquote>" if cfg["text"] else _build_welcome(user, message.chat, count)
        gif = get_random_gif("welcome")
        try:
            sent = await message.reply_animation(gif, caption=text, parse_mode=enums.ParseMode.HTML) if gif else await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
        except Exception:
            sent = await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
        asyncio.create_task(_del(sent, 86400))


@app.on_message(filters.command("setwel") & filters.group)
async def cmd_setwel(_, message: Message):
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        s = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return
    text = " ".join(message.command[1:]).strip()
    if not text:
        s = await message.reply(
            "<blockquote>⚠️ <b>Usage:</b> /setwel &lt;message&gt;\n\n<b>Placeholders:</b>\n"
            "• <code>{mention}</code> — clickable name\n• <code>{first}</code> — first name\n"
            "• <code>{username}</code> — @username\n• <code>{count}</code> — member number\n"
            "• <code>{chat}</code> — group name</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_del(s, 30))
        return
    _get(message.chat.id)["text"] = text
    s = await message.reply("<blockquote>✅ Welcome message updated!</blockquote>", parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_del(s, 15))


@app.on_message(filters.command("wel") & filters.group)
async def cmd_wel(_, message: Message):
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        s = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return
    cfg = _get(message.chat.id)
    status = "✅ ON" if cfg["on"] else "❌ OFF"
    try:
        count = await app.get_chat_members_count(message.chat.id)
    except Exception:
        count = 0
    text = "<blockquote>" + _fmt(cfg["text"], message.from_user, message.chat, count) + "</blockquote>" if cfg["text"] else _build_welcome(message.from_user, message.chat, count)
    header = f"<blockquote>📋 <b>Welcome Preview</b> [{status}]</blockquote>\n"
    s = await message.reply(header + text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    asyncio.create_task(_del(s, 30))


@app.on_message(filters.command("welon") & filters.group)
async def cmd_welon(_, message: Message):
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        s = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return
    _get(message.chat.id)["on"] = True
    s = await message.reply("<blockquote>✅ Welcome <b>enabled!</b></blockquote>", parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_del(s, 15))


@app.on_message(filters.command("weloff") & filters.group)
async def cmd_weloff(_, message: Message):
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        s = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return
    _get(message.chat.id)["on"] = False
    s = await message.reply("<blockquote>❌ Welcome <b>disabled!</b></blockquote>", parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_del(s, 15))
