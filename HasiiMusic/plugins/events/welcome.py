"""
Welcome Plugin — v3 FIXED
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

FIX: @Client.on_message / @Client.on_chat_member_updated → @app.on_* (yahi main bug tha)
"""

import re
from pyrogram import enums, filters
from pyrogram.types import (
    ChatMemberUpdated, Message,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from pymongo import MongoClient as PyMongoClient

from HasiiMusic.helpers.gif_manager import get_random_gif, register_gif_commands
from HasiiMusic import app

try:
    from HasiiMusic.core.mongo import mongodb as _db
except ImportError:
    import os
    _c = PyMongoClient(os.getenv("MONGO_DB_URI", "mongodb://localhost:27017"))
    _db = _c["HasiiMusicBot"]

welcome_col = _db["welcome_settings"]

DEFAULT_WELCOME = "💓 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 {mention} !!"


def _get_welcome(chat_id: int) -> dict:
    return welcome_col.find_one({"chat_id": chat_id}) or {
        "enabled": True, "text": DEFAULT_WELCOME, "buttons": []
    }


def _set_welcome_text(chat_id: int, text: str, buttons: list):
    welcome_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"text": text, "buttons": buttons, "enabled": True}},
        upsert=True,
    )


def _toggle_welcome(chat_id: int, enabled: bool):
    welcome_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": enabled}},
        upsert=True
    )


def _parse_buttons(text: str):
    buttons, pattern = [], r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    for label, url in re.findall(pattern, text):
        buttons.append({"label": label.strip(), "url": url.strip()})
    return re.sub(pattern, '', text).strip(), buttons


def _build_markup(buttons: list):
    if not buttons:
        return None
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(b["label"], url=b["url"])] for b in buttons]
    )


def _fill(text: str, user, chat) -> str:
    if hasattr(user, 'mention'):
        mention = user.mention
    else:
        mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    return (
        text
        .replace("{mention}", mention)
        .replace("{first_name}", user.first_name or "")
        .replace("{last_name}", user.last_name or "")
        .replace("{username}", f"@{user.username}" if user.username else user.first_name)
        .replace("{chat_title}", chat.title or "")
        .replace("{id}", str(user.id))
    )


async def _is_admin(client, chat_id, user_id) -> bool:
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status.value in ("administrator", "creator")
    except Exception:
        return False


# ─── GIF management commands ─────────────────────────────────────────────────
register_gif_commands(app, "welcome", "wel")


# ─── New member handler ───────────────────────────────────────────────────────
@app.on_chat_member_updated(filters.group)
async def on_new_member(client, update: ChatMemberUpdated):
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
    btns = settings.get("buttons", [])
    welcome_text = _fill(raw_text, user, update.chat)
    gif = get_random_gif("welcome")
    markup = _build_markup(btns)

    if gif:
        try:
            await client.send_animation(
                chat_id=update.chat.id,
                animation=gif,
                caption=welcome_text,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=markup,
            )
            return
        except Exception:
            pass

    try:
        await client.send_message(
            chat_id=update.chat.id,
            text=welcome_text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=markup,
        )
    except Exception:
        pass


# ─── /setwel ──────────────────────────────────────────────────────────────────
@app.on_message(filters.command("setwel") & filters.group)
async def setwel_cmd(client, message: Message):
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
            "<b>Button add karne ke liye:</b>\n"
            "<code>[Button Text](https://link.com)</code>\n\n"
            "<b>GIFs manage karne ke liye:</b>\n"
            "• <code>/setwelgif</code> — GIF add karo (reply karke)\n"
            "• <code>/listwelgif</code> — GIFs ki list dekho\n"
            "• <code>/rmwelgif &lt;n&gt;</code> — GIF hatao"
            "</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

    raw_input = message.text.split(None, 1)[1]
    clean_text, btns = _parse_buttons(raw_input)
    _set_welcome_text(message.chat.id, clean_text or raw_input, btns)

    preview = _fill(clean_text or raw_input, message.from_user, message.chat)
    markup = _build_markup(btns)
    confirm = (
        f"<blockquote>"
        f"✅ <b>Welcome message set ho gaya!</b>\n\n"
        f"<b>Preview:</b>\n{preview}"
    )
    if btns:
        confirm += f"\n\n🔘 <b>Buttons:</b> {len(btns)} added"
    confirm += "</blockquote>"
    await message.reply(confirm, parse_mode=enums.ParseMode.HTML, reply_markup=markup)


# ─── /stopwel ──────────────────────────────────────────────────────────────────
@app.on_message(filters.command("stopwel") & filters.group)
async def stopwel_cmd(client, message: Message):
    if not await _is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply(
            "<blockquote>❌ Sirf admins yeh kar sakte hain.</blockquote>"
        )
    _toggle_welcome(message.chat.id, False)
    await message.reply(
        "<blockquote>🔕 Welcome <b>disabled</b> kar diya.</blockquote>",
        parse_mode=enums.ParseMode.HTML
    )


# ─── /startwel ─────────────────────────────────────────────────────────────────
@app.on_message(filters.command("startwel") & filters.group)
async def startwel_cmd(client, message: Message):
    if not await _is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply(
            "<blockquote>❌ Sirf admins yeh kar sakte hain.</blockquote>"
        )
    _toggle_welcome(message.chat.id, True)
    await message.reply(
        "<blockquote>✅ Welcome <b>enabled</b> ho gaya!</blockquote>",
        parse_mode=enums.ParseMode.HTML
    )


# ─── /resetwel ─────────────────────────────────────────────────────────────────
@app.on_message(filters.command("resetwel") & filters.group)
async def resetwel_cmd(client, message: Message):
    if not await _is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply(
            "<blockquote>❌ Sirf admins yeh kar sakte hain.</blockquote>"
        )
    welcome_col.delete_one({"chat_id": message.chat.id})
    await message.reply(
        f"<blockquote>🔄 Welcome reset ho gaya!\n\n"
        f"<b>Default message:</b>\n<code>{DEFAULT_WELCOME}</code>\n\n"
        f"Default GIFs bhi wapas aa gaye.</blockquote>",
        parse_mode=enums.ParseMode.HTML
    )


# ─── /welshow ──────────────────────────────────────────────────────────────────
@app.on_message(filters.command("welshow") & filters.group)
async def welshow_cmd(client, message: Message):
    s = _get_welcome(message.chat.id)
    status = "✅ Enabled" if s.get("enabled", True) else "❌ Disabled"
    text = s.get("text", DEFAULT_WELCOME)
    btns = s.get("buttons", [])
    btn_info = f"\n🔘 <b>Buttons:</b> {', '.join(b['label'] for b in btns)}" if btns else ""
    await message.reply(
        f"<blockquote>"
        f"<b>⚙️ Welcome Settings</b>\n\n"
        f"<b>Status:</b> {status}\n"
        f"<b>Message:</b>\n<code>{text}</code>"
        f"{btn_info}\n\n"
        f"<b>Preview:</b>\n{_fill(text, message.from_user, message.chat)}\n\n"
        f"<b>GIFs:</b> /listwelgif se dekho"
        f"</blockquote>",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=_build_markup(btns),
    )
