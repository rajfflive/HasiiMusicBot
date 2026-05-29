"""
Welcome Plugin for HasiiMusicBot
Commands:
  /setwel <text>  - Set custom welcome message (use {mention} placeholder)
  /stopwel        - Disable welcome for this group
  /resetwel       - Reset to default welcome
  /welshow        - Show current welcome settings

Default welcome: 💓 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 {mention} !!
GIFs auto-rotate randomly on each welcome.
"""

import random
from pyrogram import Client, filters
from pyrogram.types import ChatMemberUpdated, Message
from pymongo import MongoClient as PyMongoClient

# ─── GIF FILE IDs (from your Telegram Raw data) ──────────────────────────────
WELCOME_GIFS = [
    "CgACAgUAAxkBAAFK1WRqF97lOizVVHm5_u0D8fXY3W-tAANCKgACBOwYVJ1ADjmP2ejnOwQ",  # download(2).gif
    "CgACAgUAAxkBAAFK1WZqF97vaBAbc9D5AAEJ3R5efIwkEpEAAkMqAAIE7BhUPG_GhsQDS7g7BA",  # ❤️.gif
    "CgACAgUAAxkBAAFK1WlqF973_CEJe0Sh7KPas3ksnWrz4wACRCoAAgTsGFR4bGRskjrbxDsE",  # download(1).gif
    "CgACAgUAAxkBAAFK1W9qF98jijDe57jE002MuXlrYhU3EwACQSoAAgTsGFRRl8lSCLWsFDsE",  # 1_2.gif
]

DEFAULT_WELCOME = "💓 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 {mention} !!"

# ─── DB helpers ──────────────────────────────────────────────────────────────
# Expects `db` to be passed in or imported from your bot's core.
# Adjust the import below to match your project's DB accessor.
try:
    from HasiiMusic.core.mongo import mongodb as db
except ImportError:
    # Fallback: standalone mongo (fill MONGO_DB_URI yourself)
    import os
    _client = PyMongoClient(os.getenv("MONGO_DB_URI", "mongodb://localhost:27017"))
    db = _client["HasiiMusicBot"]

welcome_col = db["welcome_settings"]


async def get_welcome(chat_id: int) -> dict:
    doc = welcome_col.find_one({"chat_id": chat_id})
    if not doc:
        return {"enabled": True, "text": DEFAULT_WELCOME}
    return doc


async def set_welcome_text(chat_id: int, text: str):
    welcome_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"text": text, "enabled": True}},
        upsert=True,
    )


async def toggle_welcome(chat_id: int, enabled: bool):
    welcome_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": enabled}},
        upsert=True,
    )


# ─── New member handler ───────────────────────────────────────────────────────
@Client.on_chat_member_updated(filters.group)
async def on_new_member(client: Client, update: ChatMemberUpdated):
    if not (update.new_chat_member and update.old_chat_member):
        return
    # Only trigger when someone joins (not leaves/banned/etc.)
    if update.new_chat_member.status.value not in ("member", "administrator"):
        return
    if update.old_chat_member.status.value not in ("left", "kicked"):
        return

    chat_id = update.chat.id
    settings = await get_welcome(chat_id)

    if not settings.get("enabled", True):
        return

    user = update.new_chat_member.user
    mention = user.mention  # Pyrogram auto HTML mention

    text = settings.get("text", DEFAULT_WELCOME).replace("{mention}", mention)
    gif = random.choice(WELCOME_GIFS)

    await client.send_animation(
        chat_id=chat_id,
        animation=gif,
        caption=text,
        parse_mode="html",
    )


# ─── /setwel ──────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("setwel") & filters.group)
async def setwel_cmd(client: Client, message: Message):
    # Admin check
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status.value not in ("administrator", "creator"):
        return await message.reply("❌ Only admins can set welcome message.")

    if len(message.command) < 2:
        return await message.reply(
            "**Usage:** `/setwel <your welcome text>`\n"
            "Use `{mention}` to tag the new member.\n\n"
            f"**Default:** `{DEFAULT_WELCOME}`"
        )

    text = message.text.split(None, 1)[1]
    await set_welcome_text(message.chat.id, text)
    await message.reply(f"✅ Welcome message set!\n\n**Preview:**\n{text.replace('{mention}', message.from_user.mention)}")


# ─── /stopwel ─────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("stopwel") & filters.group)
async def stopwel_cmd(client: Client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status.value not in ("administrator", "creator"):
        return await message.reply("❌ Only admins can disable welcome.")

    await toggle_welcome(message.chat.id, False)
    await message.reply("🔕 Welcome messages **disabled** for this group.")


# ─── /resetwel ────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("resetwel") & filters.group)
async def resetwel_cmd(client: Client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status.value not in ("administrator", "creator"):
        return await message.reply("❌ Only admins can reset welcome.")

    welcome_col.delete_one({"chat_id": message.chat.id})
    await message.reply(f"🔄 Welcome reset to default:\n\n`{DEFAULT_WELCOME}`")


# ─── /welshow ─────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("welshow") & filters.group)
async def welshow_cmd(client: Client, message: Message):
    settings = await get_welcome(message.chat.id)
    status = "✅ Enabled" if settings.get("enabled", True) else "❌ Disabled"
    text = settings.get("text", DEFAULT_WELCOME)
    await message.reply(
        f"**Welcome Settings**\n"
        f"**Status:** {status}\n"
        f"**Message:**\n`{text}`"
    )
