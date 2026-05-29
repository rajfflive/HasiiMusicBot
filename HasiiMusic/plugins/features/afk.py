"""
AFK Plugin — v2 with GIF Manager
Commands:
  /afk [reason]  - Go AFK with big styled message + GIF
  /back          - Manually return from AFK

GIF Management (owner/sudo/admin only):
  /setafkgif      - Reply to GIF → add to AFK list
  /setafkgif naam - Reply to GIF + give custom name
  /rmafkgif <n>   - Remove AFK GIF by number
  /listafkgif     - See all AFK GIFs with numbers
"""

import time
from datetime import timedelta
from pyrogram import filters
from pyrogram.types import Message
from pymongo import MongoClient as PyMongoClient

# ✅ FIX: Use the actual client instance 'app'
from HasiiMusic import app
from HasiiMusic.helpers.gif_manager import get_random_gif, register_gif_commands

try:
    from HasiiMusic.core.mongo import mongodb as db
except ImportError:
    import os
    _client = PyMongoClient(os.getenv("MONGO_DB_URI", "mongodb://localhost:27017"))
    db = _client["HasiiMusicBot"]

afk_col = db["afk_users"]


def _time_fmt(seconds: int) -> str:
    td = timedelta(seconds=seconds)
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


def is_afk(user_id: int):
    return afk_col.find_one({"user_id": user_id})


def set_afk(user_id: int, reason: str):
    afk_col.update_one(
        {"user_id": user_id},
        {"$set": {"reason": reason, "since": int(time.time())}},
        upsert=True,
    )


def clear_afk(user_id: int):
    afk_col.delete_one({"user_id": user_id})


# ─── GIF management commands ─────────────────────────────────────────────────
# ✅ FIX: Pass correct app instance
register_gif_commands(app, "afk", "afk")


# ─── /afk ────────────────────────────────────────────────────────────────────
# ✅ FIX: Use @app.on_message instead of @Client.on_message
@app.on_message(filters.command("afk") & (filters.group | filters.private))
async def afk_cmd(client, message: Message):
    user = message.from_user
    reason = " ".join(message.command[1:]) if len(message.command) > 1 else "Koi reason nahi diya."
    set_afk(user.id, reason)

    gif = get_random_gif("afk")
    caption = (
        f"<blockquote>"
        f"😴 <b>{user.first_name} AFK ho gaya!</b>\n\n"
        f"╔══════════════════╗\n"
        f"║  💤  A F K  M O D E  💤  ║\n"
        f"╚══════════════════╝\n\n"
        f"👤 <b>User:</b> {user.mention}\n"
        f"📝 <b>Reason:</b> {reason}\n"
        f"⏰ <b>Gaya:</b> Abhi abhi\n\n"
        f"<i>Jab tak reply na karo, samjho AFK hai 🌙</i>"
        f"</blockquote>"
    )
    
    # ✅ FIX: Send GIF only if available, else send only text
    if gif:
        await message.reply_animation(gif, caption=caption, parse_mode="html")
    else:
        await message.reply_text(caption, parse_mode="html")


# ─── /back ───────────────────────────────────────────────────────────────────
@app.on_message(filters.command("back") & (filters.group | filters.private))
async def back_cmd(client, message: Message):
    user = message.from_user
    doc = is_afk(user.id)
    if not doc:
        return await message.reply(
            "<blockquote>ℹ️ Tum AFK mein nahi the abhi.</blockquote>",
            parse_mode="html"
        )

    duration = _time_fmt(int(time.time()) - doc["since"])
    clear_afk(user.id)
    await message.reply(
        f"<blockquote>"
        f"✅ <b>Welcome Back, {user.mention}!</b>\n\n"
        f"⏳ Tum <b>{duration}</b> ke liye AFK the.\n"
        f"<i>Khush aamdeed! 🎉</i>"
        f"</blockquote>",
        parse_mode="html",
    )


# ─── Auto-return ──────────────────────────────────────────────────────────────
@app.on_message(filters.group & ~filters.bot & ~filters.command(["afk"]))
async def auto_back(client, message: Message):
    if not message.from_user:
        return
    doc = is_afk(message.from_user.id)
    if doc:
        duration = _time_fmt(int(time.time()) - doc["since"])
        clear_afk(message.from_user.id)
        await message.reply(
            f"<blockquote>"
            f"✅ <b>Welcome Back, {message.from_user.mention}!</b>\n\n"
            f"⏳ Tum <b>{duration}</b> ke liye AFK the.\n"
            f"<i>Wapas aa gaye! 🎉</i>"
            f"</blockquote>",
            parse_mode="html",
        )


# ─── Mention notify ───────────────────────────────────────────────────────────
@app.on_message(filters.group & ~filters.bot)
async def mention_check(client, message: Message):
    if not message.from_user:
        return
    targets = []
    if message.reply_to_message and message.reply_to_message.from_user:
        targets.append(message.reply_to_message.from_user)
    if message.entities:
        for ent in message.entities:
            if ent.type.value in ("mention", "text_mention"):
                if ent.user:
                    targets.append(ent.user)
                elif message.text:
                    uname = message.text[ent.offset + 1: ent.offset + ent.length]
                    try:
                        targets.append(await client.get_users(uname))
                    except Exception:
                        pass

    for target in targets:
        if not target or target.id == message.from_user.id:
            continue
        doc = is_afk(target.id)
        if doc:
            duration = _time_fmt(int(time.time()) - doc["since"])
            await message.reply(
                f"<blockquote>"
                f"⚠️ <b>{target.first_name} AFK mein hai!</b>\n\n"
                f"😴 <b>Reason:</b> {doc.get('reason', 'Koi reason nahi.')}\n"
                f"⏰ <b>Since:</b> {duration} pehle se\n\n"
                f"<i>Thoda wait karo, woh jald wapas aayega 🌙</i>"
                f"</blockquote>",
                parse_mode="html",
            )
