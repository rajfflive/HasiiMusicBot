"""
Welcome Plugin — v3 FINAL (All English)
Place at: HasiiMusic/plugins/features/welcome.py

Commands (admin only):
  /setwelcome <text>   - Set custom welcome message
                         Placeholders: {mention}, {first}, {last}, {username}, {count}, {chat}
  /resetwelcome        - Reset to default welcome message
  /welcome             - Show current welcome message (preview)
  /setgoodbye <text>   - Set custom goodbye message
  /resetgoodbye        - Reset to default goodbye
  /goodbye             - Show current goodbye message (preview)
  /welcometoggle       - Enable/disable welcome messages
  /goodbyetoggle       - Enable/disable goodbye messages

Note: Uses "welcome" gif for joins, "goodbye" gif for leaves.
Auto-delete: All welcome/goodbye messages deleted after 24 hours.
"""

import asyncio

from pyrogram import enums, filters
from pyrogram.types import ChatMemberUpdated, Message

from HasiiMusic import app
from HasiiMusic.helpers.gif_manager import get_random_gif

# ── Storage ──────────────────────────────────────────────────────────────────
# { chat_id: { "welcome": str|None, "goodbye": str|None, "welcome_on": bool, "goodbye_on": bool } }
_settings: dict[int, dict] = {}

WELCOME_DELETE_DELAY = 120  # 24 hours

DEFAULT_WELCOME = (
    "👋 Welcome to <b>{chat}</b>, {mention}!\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "🎉 You are member <b>#{count}</b>.\n"
    "📜 Please read the group rules and enjoy your stay!"
)

DEFAULT_GOODBYE = (
    "👋 <b>{first}</b> has left the group.\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "😢 We'll miss you! Hope to see you back soon."
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _settings_for(chat_id: int) -> dict:
    if chat_id not in _settings:
        _settings[chat_id] = {
            "welcome": None,
            "goodbye": None,
            "welcome_on": True,
            "goodbye_on": True,
        }
    return _settings[chat_id]


def _mention_html(user) -> str:
    name = (user.first_name or "User").replace("<", "&lt;").replace(">", "&gt;")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"


def _format_msg(template: str, user, chat, count: int) -> str:
    first = (user.first_name or "").replace("<", "&lt;").replace(">", "&gt;")
    last = (user.last_name or "").replace("<", "&lt;").replace(">", "&gt;")
    username = f"@{user.username}" if user.username else first
    chat_name = (chat.title or "this group").replace("<", "&lt;").replace(">", "&gt;")
    mention = _mention_html(user)

    return (
        template
        .replace("{mention}", mention)
        .replace("{first}", first)
        .replace("{last}", last)
        .replace("{username}", username)
        .replace("{count}", str(count))
        .replace("{chat}", chat_name)
    )


async def _is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


async def _auto_delete(msg: Message, delay: int = WELCOME_DELETE_DELAY):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


async def _send_with_gif(chat_id: int, gif_type: str, text: str, reply_to=None):
    gif = get_random_gif(gif_type)
    kwargs = dict(parse_mode=enums.ParseMode.HTML, disable_notification=True)
    if reply_to:
        kwargs["reply_to_message_id"] = reply_to

    try:
        if gif:
            sent = await app.send_animation(chat_id, gif, caption=text, **kwargs)
        else:
            sent = await app.send_message(chat_id, text, disable_web_page_preview=True, **kwargs)
    except Exception:
        sent = await app.send_message(
            chat_id, text, disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML, disable_notification=True
        )

    asyncio.create_task(_auto_delete(sent, WELCOME_DELETE_DELAY))


# ── New Member Handler ────────────────────────────────────────────────────────

@app.on_chat_member_updated(filters.group)
async def member_updated_handler(_, update: ChatMemberUpdated):
    if not update.new_chat_member or not update.old_chat_member:
        return

    chat = update.chat
    chat_id = chat.id
    cfg = _settings_for(chat_id)

    old_status = update.old_chat_member.status
    new_status = update.new_chat_member.status
    user = update.new_chat_member.user

    if not user or user.is_bot:
        return

    # ── JOINED ──
    joined = (
        old_status == enums.ChatMemberStatus.LEFT
        or old_status == enums.ChatMemberStatus.BANNED
    ) and new_status == enums.ChatMemberStatus.MEMBER

    # ── LEFT ──
    left = (
        old_status == enums.ChatMemberStatus.MEMBER
        or old_status == enums.ChatMemberStatus.ADMINISTRATOR
    ) and (
        new_status == enums.ChatMemberStatus.LEFT
        or new_status == enums.ChatMemberStatus.BANNED
    )

    if joined and cfg["welcome_on"]:
        try:
            count = await app.get_chat_members_count(chat_id)
        except Exception:
            count = 0

        template = cfg["welcome"] or DEFAULT_WELCOME
        text = "<blockquote>" + _format_msg(template, user, chat, count) + "</blockquote>"
        await _send_with_gif(chat_id, "welcome", text)

    elif left and cfg["goodbye_on"]:
        template = cfg["goodbye"] or DEFAULT_GOODBYE
        text = "<blockquote>" + _format_msg(template, user, chat, 0) + "</blockquote>"
        await _send_with_gif(chat_id, "goodbye", text)


# ── /setwelcome ───────────────────────────────────────────────────────────────

@app.on_message(filters.command("setwelcome") & filters.group)
async def cmd_setwelcome(_, message: Message):
    user = message.from_user
    if not user or not await _is_admin(message.chat.id, user.id):
        sent = await message.reply(
            "<blockquote>🚫 Only admins can set the welcome message.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 10))
        return

    text = " ".join(message.command[1:]).strip()
    if not text:
        sent = await message.reply(
            "<blockquote>⚠️ Usage: /setwelcome &lt;message&gt;\n\n"
            "Placeholders:\n"
            "  {mention} — clickable name\n"
            "  {first} — first name\n"
            "  {last} — last name\n"
            "  {username} — @username\n"
            "  {count} — member count\n"
            "  {chat} — group name</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 30))
        return

    cfg = _settings_for(message.chat.id)
    cfg["welcome"] = text

    sent = await message.reply(
        "<blockquote>✅ Welcome message updated!</blockquote>",
        parse_mode=enums.ParseMode.HTML,
    )
    asyncio.create_task(_auto_delete(sent, 30))


# ── /resetwelcome ─────────────────────────────────────────────────────────────

@app.on_message(filters.command("resetwelcome") & filters.group)
async def cmd_resetwelcome(_, message: Message):
    user = message.from_user
    if not user or not await _is_admin(message.chat.id, user.id):
        sent = await message.reply(
            "<blockquote>🚫 Admins only.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 10))
        return

    _settings_for(message.chat.id)["welcome"] = None
    sent = await message.reply(
        "<blockquote>♻️ Welcome message reset to default.</blockquote>",
        parse_mode=enums.ParseMode.HTML,
    )
    asyncio.create_task(_auto_delete(sent, 30))


# ── /welcome (preview) ────────────────────────────────────────────────────────

@app.on_message(filters.command("welcome") & filters.group)
async def cmd_welcome_preview(_, message: Message):
    user = message.from_user
    if not user or not await _is_admin(message.chat.id, user.id):
        sent = await message.reply(
            "<blockquote>🚫 Admins only.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 10))
        return

    cfg = _settings_for(message.chat.id)
    status = "✅ Enabled" if cfg["welcome_on"] else "❌ Disabled"
    template = cfg["welcome"] or DEFAULT_WELCOME

    try:
        count = await app.get_chat_members_count(message.chat.id)
    except Exception:
        count = 0

    preview = _format_msg(template, user, message.chat, count)

    text = (
        f"<blockquote>"
        f"🔍 <b>Welcome Preview</b> ({status})\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{preview}"
        f"</blockquote>"
    )
    sent = await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    asyncio.create_task(_auto_delete(sent, 30))


# ── /setgoodbye ───────────────────────────────────────────────────────────────

@app.on_message(filters.command("setgoodbye") & filters.group)
async def cmd_setgoodbye(_, message: Message):
    user = message.from_user
    if not user or not await _is_admin(message.chat.id, user.id):
        sent = await message.reply(
            "<blockquote>🚫 Admins only.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 10))
        return

    text = " ".join(message.command[1:]).strip()
    if not text:
        sent = await message.reply(
            "<blockquote>⚠️ Usage: /setgoodbye &lt;message&gt;\n\n"
            "Placeholders: {mention} {first} {last} {username} {chat}</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 30))
        return

    _settings_for(message.chat.id)["goodbye"] = text
    sent = await message.reply(
        "<blockquote>✅ Goodbye message updated!</blockquote>",
        parse_mode=enums.ParseMode.HTML,
    )
    asyncio.create_task(_auto_delete(sent, 30))


# ── /resetgoodbye ─────────────────────────────────────────────────────────────

@app.on_message(filters.command("resetgoodbye") & filters.group)
async def cmd_resetgoodbye(_, message: Message):
    user = message.from_user
    if not user or not await _is_admin(message.chat.id, user.id):
        sent = await message.reply(
            "<blockquote>🚫 Admins only.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 10))
        return

    _settings_for(message.chat.id)["goodbye"] = None
    sent = await message.reply(
        "<blockquote>♻️ Goodbye message reset to default.</blockquote>",
        parse_mode=enums.ParseMode.HTML,
    )
    asyncio.create_task(_auto_delete(sent, 30))


# ── /goodbye (preview) ────────────────────────────────────────────────────────

@app.on_message(filters.command("goodbye") & filters.group)
async def cmd_goodbye_preview(_, message: Message):
    user = message.from_user
    if not user or not await _is_admin(message.chat.id, user.id):
        sent = await message.reply(
            "<blockquote>🚫 Admins only.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 10))
        return

    cfg = _settings_for(message.chat.id)
    status = "✅ Enabled" if cfg["goodbye_on"] else "❌ Disabled"
    template = cfg["goodbye"] or DEFAULT_GOODBYE
    preview = _format_msg(template, user, message.chat, 0)

    text = (
        f"<blockquote>"
        f"🔍 <b>Goodbye Preview</b> ({status})\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{preview}"
        f"</blockquote>"
    )
    sent = await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    asyncio.create_task(_auto_delete(sent, 30))


# ── /welcometoggle ────────────────────────────────────────────────────────────

@app.on_message(filters.command("welcometoggle") & filters.group)
async def cmd_welcometoggle(_, message: Message):
    user = message.from_user
    if not user or not await _is_admin(message.chat.id, user.id):
        sent = await message.reply(
            "<blockquote>🚫 Admins only.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 10))
        return

    cfg = _settings_for(message.chat.id)
    cfg["welcome_on"] = not cfg["welcome_on"]
    state = "✅ Enabled" if cfg["welcome_on"] else "❌ Disabled"

    sent = await message.reply(
        f"<blockquote>🔔 Welcome messages: <b>{state}</b></blockquote>",
        parse_mode=enums.ParseMode.HTML,
    )
    asyncio.create_task(_auto_delete(sent, 30))


# ── /goodbyetoggle ────────────────────────────────────────────────────────────

@app.on_message(filters.command("goodbyetoggle") & filters.group)
async def cmd_goodbyetoggle(_, message: Message):
    user = message.from_user
    if not user or not await _is_admin(message.chat.id, user.id):
        sent = await message.reply(
            "<blockquote>🚫 Admins only.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 10))
        return

    cfg = _settings_for(message.chat.id)
    cfg["goodbye_on"] = not cfg["goodbye_on"]
    state = "✅ Enabled" if cfg["goodbye_on"] else "❌ Disabled"

    sent = await message.reply(
        f"<blockquote>👋 Goodbye messages: <b>{state}</b></blockquote>",
        parse_mode=enums.ParseMode.HTML,
    )
    asyncio.create_task(_auto_delete(sent, 30))
