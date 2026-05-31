"""
Welcome Plugin — v4 SHORT
Place at: HasiiMusic/plugins/features/welcome.py

Commands (admin only):
  /setwel <text>   - Set welcome message
  /wel             - Preview current welcome
  /welon           - Enable welcome
  /weloff          - Disable welcome

Placeholders: {mention} {first} {username} {count} {chat}
"""

import asyncio

from pyrogram import enums, filters
from pyrogram.types import Message

from HasiiMusic import app
from HasiiMusic.helpers.gif_manager import get_random_gif

_cfg: dict[int, dict] = {}

DEFAULT_WELCOME = (
    "👋 Welcome {mention} to <b>{chat}</b>!\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "🎉 You are member <b>#{count}</b>.\n"
    "📜 Please follow the group rules and enjoy!"
)


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


async def _is_admin(chat_id: int, user_id: int) -> bool:
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


# ── Join handler ──────────────────────────────────────────────────────────────

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

        template = cfg["text"] or DEFAULT_WELCOME
        text = "<blockquote>" + _fmt(template, user, message.chat, count) + "</blockquote>"

        gif = get_random_gif("welcome")
        try:
            if gif:
                sent = await message.reply_animation(gif, caption=text, parse_mode=enums.ParseMode.HTML)
            else:
                sent = await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
        except Exception:
            sent = await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)

        asyncio.create_task(_del(sent, 86400))


# ── /setwel ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("setwel") & filters.group)
async def cmd_setwel(_, message: Message):
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(sent, 10))
        return

    text = " ".join(message.command[1:]).strip()
    if not text:
        sent = await message.reply(
            "<blockquote>⚠️ <b>Usage:</b> /setwel &lt;message&gt;\n\n"
            "Placeholders:\n{mention} {first} {username} {count} {chat}</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_del(sent, 30))
        return

    _get(message.chat.id)["text"] = text
    sent = await message.reply("<blockquote>✅ Welcome message set!</blockquote>", parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_del(sent, 15))


# ── /wel (preview) ────────────────────────────────────────────────────────────

@app.on_message(filters.command("wel") & filters.group)
async def cmd_wel(_, message: Message):
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(sent, 10))
        return

    cfg = _get(message.chat.id)
    status = "✅ ON" if cfg["on"] else "❌ OFF"
    template = cfg["text"] or DEFAULT_WELCOME

    try:
        count = await app.get_chat_members_count(message.chat.id)
    except Exception:
        count = 0

    preview = _fmt(template, message.from_user, message.chat, count)
    text = (
        f"<blockquote>"
        f"📋 <b>Welcome Preview</b> [{status}]\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{preview}"
        f"</blockquote>"
    )
    sent = await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    asyncio.create_task(_del(sent, 30))


# ── /welon ────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("welon") & filters.group)
async def cmd_welon(_, message: Message):
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(sent, 10))
        return

    _get(message.chat.id)["on"] = True
    sent = await message.reply("<blockquote>✅ Welcome messages <b>enabled!</b></blockquote>", parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_del(sent, 15))


# ── /weloff ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("weloff") & filters.group)
async def cmd_weloff(_, message: Message):
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(sent, 10))
        return

    _get(message.chat.id)["on"] = False
    sent = await message.reply("<blockquote>❌ Welcome messages <b>disabled!</b></blockquote>", parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_del(sent, 15))
