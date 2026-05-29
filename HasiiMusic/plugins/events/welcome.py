"""
Welcome Plugin — v2 with GIF Manager
Commands:
  /setwel <text>   - Set custom welcome message
  /stopwel         - Disable welcome
  /startwel        - Re-enable welcome
  /resetwel        - Reset to default
  /welshow         - Show current settings + preview

GIF Management (owner/sudo/admin only):
  /setwelgif       - Reply to GIF → add to welcome list
  /setwelgif naam  - Reply to GIF + custom name
  /rmwelgif <n>    - Remove welcome GIF by number
  /listwelgif      - See all welcome GIFs with numbers
"""

import re
from pyrogram import Client, filters
from pyrogram.types import (
    ChatMemberUpdated, Message,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from pymongo import MongoClient as PyMongoClient

from HasiiMusic.helpers.gif_manager import get_random_gif, register_gif_commands

DEFAULT_WELCOME = "💓 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 {mention} !!"

try:
    from HasiiMusic.core.mongo import mongodb as db
except ImportError:
    import os
    _client = PyMongoClient(os.getenv("MONGO_DB_URI", "mongodb://localhost:27017"))
    db = _client["HasiiMusicBot"]

welcome_col = db["welcome_settings"]


def _get_welcome(chat_id: int) -> dict:
    return welcome_col.find_one({"chat_id": chat_id}) or {"enabled": True, "text": DEFAULT_WELCOME, "buttons": []}


def _set_welcome_text(chat_id: int, text: str, buttons: list):
    welcome_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"text": text, "buttons": buttons, "enabled": True}},
        upsert=True,
    )


def _toggle_welcome(chat_id: int, enabled: bool):
    welcome_col.update_one({"chat_id": chat_id}, {"$set": {"enabled": enabled}}, upsert=True)


def _parse_buttons(text: str):
    buttons, pattern = [], r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    for label, url in re.findall(pattern, text):
        buttons.append({"label": label.strip(), "url": url.strip()})
    return re.sub(pattern, '', text).strip(), buttons


def _build_markup(buttons: list):
    if not buttons:
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton(b["label"], url=b["url"])] for b in buttons])


def _fill(text: str, user, chat) -> str:
    mention = user.mention if hasattr(user, 'mention') else f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    return (text
            .replace("{mention}", mention)
            .replace("{first_name}", user.first_name or "")
            .replace("{last_name}", user.last_name or "")
            .replace("{username}", f"@{user.username}" if user.username else user.first_name)
            .replace("{chat_title}", chat.title or "")
            .replace("{id}", str(user.id)))


async def _is_admin(client, chat_id, user_id):
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status.value in ("administrator", "creator")
    except Exception:
        return False


# ─── GIF management commands ─────────────────────────────────────────────────
try:
    from HasiiMusic import app as _app
    register_gif_commands(_app, "welcome", "wel")
except Exception:
    pass


# ─── New member handler ───────────────────────────────────────────────────────
@Client.on_chat_member_updated(filters.group)
async def on_new_member(client: Client, update: ChatMemberUpdated):
    if not (update.new_chat_member and update.old_chat_member):
        return
    if update.new_chat_member.status.value not in ("member", "administrator"):
        return
    if update.old_chat_member.status.value not in ("left", "kicked"):
        return

    settings = _get_welcome(update.chat.id)
    if not settings.get("enabled", True):
        return

    user = update.new_chat_member.user
    if not user or user.is_bot:
        return

    raw_text = settings.get("text", DEFAULT_WELCOME)
    buttons = settings.get("buttons", [])
    welcome_text = _fill(raw_text, user, update.chat)
    gif = get_random_gif("welcome")
    markup = _build_markup(buttons)

    try:
        await client.send_animation(
            chat_id=update.chat.id, animation=gif,
            caption=welcome_text, parse_mode="html", reply_markup=markup,
        )
    except Exception:
        try:
            await client.send_message(
                chat_id=update.chat.id, text=welcome_text,
                parse_mode="html", reply_markup=markup,
            )
        except Exception:
            pass


# ─── /setwel ──────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("setwel") & filters.group)
async def setwel_cmd(client: Client, message: Message):
    if not await _is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply(
            "<blockquote>❌ Sirf admins welcome message set kar sakte hain.</blockquote>"
        )
    if len(message.command) < 2:
        return await message.reply(
            "<blockquote>"
            "<b>📋 Welcome Setup</b>\n\n"
            "<b>Usage:</b> <code>/setwel apna message</code>\n\n"
            "<b>Placeholders:</b>\n"
            "• <code>{mention}</code> — new member ka mention\n"
            "• <code>{first_name}</code> — first name\n"
            "• <code>{username}</code> — @username\n"
            "• <code>{chat_title}</code> — group name\n\n"
            "<b>Button:</b> <code>[Text](https://link.com)</code>\n\n"
            "<b>GIFs manage karne ke liye:</b>\n"
            "• /setwelgif — GIF add karo\n"
            "• /listwelgif — GIFs dekho\n"
            "• /rmwelgif &lt;n&gt; — GIF hatao"
            "</blockquote>",
            parse_mode="html"
        )

    raw_input = message.text.split(None, 1)[1]
    clean_text, buttons = _parse_buttons(raw_input)
    _set_welcome_text(message.chat.id, clean_text or raw_input, buttons)

    preview = _fill(clean_text or raw_input, message.from_user, message.chat)
    markup = _build_markup(buttons)
    confirm = (
        f"<blockquote>"
        f"✅ <b>Welcome message set!</b>\n\n"
        f"<b>Preview:</b>\n{preview}"
    )
    if buttons:
        confirm += f"\n\n🔘 <b>Buttons:</b> {len(buttons)} added"
    confirm += "</blockquote>"
    await message.reply(confirm, parse_mode="html", reply_markup=markup)


# ─── /stopwel ──────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("stopwel") & filters.group)
async def stopwel_cmd(client: Client, message: Message):
    if not await _is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply(
            "<blockquote>❌ Sirf admins yeh kar sakte hain.</blockquote>"
        )
    _toggle_welcome(message.chat.id, False)
    await message.reply(
        "<blockquote>🔕 Welcome <b>disabled</b> kar diya.</blockquote>",
        parse_mode="html"
    )


# ─── /startwel ─────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("startwel") & filters.group)
async def startwel_cmd(client: Client, message: Message):
    if not await _is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply(
            "<blockquote>❌ Sirf admins yeh kar sakte hain.</blockquote>"
        )
    _toggle_welcome(message.chat.id, True)
    await message.reply(
        "<blockquote>✅ Welcome <b>enabled</b> ho gaya!</blockquote>",
        parse_mode="html"
    )


# ─── /resetwel ─────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("resetwel") & filters.group)
async def resetwel_cmd(client: Client, message: Message):
    if not await _is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply(
            "<blockquote>❌ Sirf admins yeh kar sakte hain.</blockquote>"
        )
    welcome_col.delete_one({"chat_id": message.chat.id})
    await message.reply(
        f"<blockquote>🔄 Welcome reset ho gaya!\n\n"
        f"<b>Default:</b>\n<code>{DEFAULT_WELCOME}</code></blockquote>",
        parse_mode="html"
    )


# ─── /welshow ──────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("welshow") & filters.group)
async def welshow_cmd(client: Client, message: Message):
    s = _get_welcome(message.chat.id)
    status = "✅ Enabled" if s.get("enabled", True) else "❌ Disabled"
    text = s.get("text", DEFAULT_WELCOME)
    buttons = s.get("buttons", [])
    btn_info = f"\n🔘 <b>Buttons:</b> {', '.join(b['label'] for b in buttons)}" if buttons else ""
    await message.reply(
        f"<blockquote>"
        f"<b>⚙️ Welcome Settings</b>\n\n"
        f"<b>Status:</b> {status}\n"
        f"<b>Message:</b>\n<code>{text}</code>"
        f"{btn_info}\n\n"
        f"<b>Preview:</b>\n{_fill(text, message.from_user, message.chat)}"
        f"</blockquote>",
        parse_mode="html",
        reply_markup=_build_markup(buttons),
    )
