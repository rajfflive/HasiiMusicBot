"""
AFK Plugin for HasiiMusicBot
Commands:
  /afk [reason]  - Go AFK (optionally with a reason)
  /back          - Manually come back from AFK (also auto-triggers on any message)

When an AFK user is mentioned/replied-to, bot notifies with how long they've been AFK.
AFK GIFs auto-rotate on /afk command.
"""

import time
from datetime import timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient as PyMongoClient

# ─── AFK GIF FILE IDs ────────────────────────────────────────────────────────
AFK_GIFS = [
    "CgACAgQAAxkBAAFK1XtqF9_2tJ3gO-M4s5maiJUEhyOj8QACYAYAArVNxVPwrkrEYMP32DsE",  # meryl-sleeping
    "CgACAgQAAxkBAAFK1X1qF9_9eF2EuPslGxXRc_IJjJakuwACcgoAAsxW1VF_E0ajtS9OWDsE",  # agleia-afk
    "CgACAgQAAxkBAAFK1X9qF-AEMI7JIAND7ETKRFm39cuMOgAC3QUAArsSfFKCBG-3ncRIijsE",  # nemesis-sleeping
]

# ─── DB ──────────────────────────────────────────────────────────────────────
try:
    from HasiiMusic.core.mongo import mongodb as db
except ImportError:
    import os
    _client = PyMongoClient(os.getenv("MONGO_DB_URI", "mongodb://localhost:27017"))
    db = _client["HasiiMusicBot"]

afk_col = db["afk_users"]


def _time_fmt(seconds: int) -> str:
    """Convert seconds to human-readable duration."""
    td = timedelta(seconds=seconds)
    days = td.days
    hours, rem = divmod(td.seconds, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def is_afk(user_id: int) -> dict | None:
    return afk_col.find_one({"user_id": user_id})


def set_afk(user_id: int, reason: str):
    afk_col.update_one(
        {"user_id": user_id},
        {"$set": {"reason": reason, "since": int(time.time())}},
        upsert=True,
    )


def clear_afk(user_id: int):
    afk_col.delete_one({"user_id": user_id})


# ─── /afk ────────────────────────────────────────────────────────────────────
import random

@Client.on_message(filters.command("afk") & (filters.group | filters.private))
async def afk_cmd(client: Client, message: Message):
    user = message.from_user
    reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason given."
    set_afk(user.id, reason)

    gif = random.choice(AFK_GIFS)
    caption = (
        f"😴 {user.mention} is now **AFK**!\n"
        f"**Reason:** {reason}"
    )

    if message.chat.type.value == "private":
        await client.send_animation(message.chat.id, gif, caption=caption, parse_mode="html")
    else:
        await client.send_animation(message.chat.id, gif, caption=caption, parse_mode="html")


# ─── /back (manual return) ───────────────────────────────────────────────────
@Client.on_message(filters.command("back") & (filters.group | filters.private))
async def back_cmd(client: Client, message: Message):
    user = message.from_user
    doc = is_afk(user.id)
    if not doc:
        return await message.reply("You are not AFK right now.")

    duration = _time_fmt(int(time.time()) - doc["since"])
    clear_afk(user.id)
    await message.reply(
        f"✅ Welcome back, {user.mention}!\n"
        f"You were AFK for **{duration}**.",
        parse_mode="html",
    )


# ─── Auto-return when AFK user sends a message ───────────────────────────────
@Client.on_message(
    filters.group & ~filters.bot & ~filters.command(["afk"])
)
async def auto_back(client: Client, message: Message):
    if not message.from_user:
        return
    user = message.from_user
    doc = is_afk(user.id)
    if doc:
        duration = _time_fmt(int(time.time()) - doc["since"])
        clear_afk(user.id)
        await message.reply(
            f"✅ Welcome back, {user.mention}! You were AFK for **{duration}**.",
            parse_mode="html",
        )


# ─── Notify when AFK user is mentioned or replied to ─────────────────────────
@Client.on_message(filters.group & ~filters.bot)
async def mention_check(client: Client, message: Message):
    targets = []

    # Check reply-to
    if message.reply_to_message and message.reply_to_message.from_user:
        targets.append(message.reply_to_message.from_user)

    # Check text mentions (HTML/markdown @username or tg-mention)
    if message.entities:
        for ent in message.entities:
            if ent.type.value in ("mention", "text_mention"):
                if ent.user:
                    targets.append(ent.user)
                elif message.text:
                    # @username — resolve
                    username = message.text[ent.offset + 1 : ent.offset + ent.length]
                    try:
                        u = await client.get_users(username)
                        targets.append(u)
                    except Exception:
                        pass

    for target in targets:
        if not target or target.id == message.from_user.id:
            continue
        doc = is_afk(target.id)
        if doc:
            duration = _time_fmt(int(time.time()) - doc["since"])
            reason = doc.get("reason", "No reason given.")
            await message.reply(
                f"⚠️ {target.mention} is **AFK** right now!\n"
                f"**Reason:** {reason}\n"
                f"**Since:** {duration} ago",
                parse_mode="html",
            )
