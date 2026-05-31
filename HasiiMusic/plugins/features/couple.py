"""
Couple Plugin — v3 FINAL (All English)
Place at: HasiiMusic/plugins/features/couple.py

Commands:
  /couple          - Randomly pair two members as today's couple
  /mycouple        - Show your current couple partner
  /couplebreak     - Break your current couple pairing
  /coupletop       - Show top couples by pair count

Note: Couple changes daily (auto-reset at midnight). Reply IS sent. Uses "couple" gif.
"""

import asyncio
import random
import time
from datetime import datetime, date

from pyrogram import enums, filters
from pyrogram.types import Message

from HasiiMusic import app
from HasiiMusic.helpers.gif_manager import get_random_gif

# ── Storage ──────────────────────────────────────────────────────────────────
# { chat_id: { "date": "YYYY-MM-DD", "pair": (uid1, uid2), "count": {uid: int} } }
_couples: dict[int, dict] = {}

COUPLE_DELETE_DELAY = 86400  # 24 hours


# ── Helpers ──────────────────────────────────────────────────────────────────

def _mention(user) -> str:
    name = (user.first_name or "User").replace("<", "&lt;").replace(">", "&gt;")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"


def _today() -> str:
    return date.today().isoformat()


def _get_couple(chat_id: int) -> tuple[int, int] | None:
    data = _couples.get(chat_id)
    if not data:
        return None
    if data.get("date") != _today():
        # Day changed — reset pair but keep history
        _couples[chat_id]["pair"] = None
        _couples[chat_id]["date"] = _today()
        return None
    return data.get("pair")


def _set_couple(chat_id: int, uid1: int, uid2: int):
    if chat_id not in _couples:
        _couples[chat_id] = {"date": _today(), "pair": None, "count": {}}
    _couples[chat_id]["date"] = _today()
    _couples[chat_id]["pair"] = (uid1, uid2)
    # Increment pair count
    for uid in (uid1, uid2):
        _couples[chat_id]["count"][uid] = _couples[chat_id]["count"].get(uid, 0) + 1


async def _auto_delete(msg: Message, delay: int = COUPLE_DELETE_DELAY):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


# ── /couple ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("couple") & filters.group)
async def cmd_couple(_, message: Message):
    chat_id = message.chat.id

    # Check if today's couple already set
    existing = _get_couple(chat_id)
    if existing:
        try:
            u1 = await app.get_users(existing[0])
            u2 = await app.get_users(existing[1])
            gif = get_random_gif("couple")
            text = (
                f"<blockquote>"
                f"💑 <b>Today's Couple is Already Set!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💘 {_mention(u1)}\n"
                f"💝 {_mention(u2)}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"❤️ Come back tomorrow for a new couple!"
                f"</blockquote>"
            )
            if gif:
                sent = await message.reply_animation(
                    gif, caption=text, parse_mode=enums.ParseMode.HTML
                )
            else:
                sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
            asyncio.create_task(_auto_delete(sent, COUPLE_DELETE_DELAY))
        except Exception as e:
            await message.reply(
                f"<blockquote>❌ Error fetching couple info: {e}</blockquote>",
                parse_mode=enums.ParseMode.HTML,
            )
        return

    # Fetch group members
    members = []
    try:
        async for m in app.get_chat_members(chat_id):
            if m.user and not m.user.is_bot and not m.user.is_deleted:
                members.append(m.user)
    except Exception as e:
        sent = await message.reply(
            f"<blockquote>❌ <b>Failed to fetch members!</b>\n\n"
            f"Make sure the bot is admin with Add Members permission.\n"
            f"<code>{e}</code></blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 60))
        return

    if len(members) < 2:
        sent = await message.reply(
            "<blockquote>❌ Need at least 2 non-bot members to make a couple!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 30))
        return

    # Pick two random distinct members
    u1, u2 = random.sample(members, 2)
    _set_couple(chat_id, u1.id, u2.id)

    gif = get_random_gif("couple")

    love_lines = [
        "A match written in the stars! 🌟",
        "Love is in the air! 💨❤️",
        "The algorithm has spoken! 🤖💘",
        "Destiny brought them together! 🔮",
        "Today's dream team! 🏆💑",
        "Chemistry detected! 🧪❤️",
        "Soulmates for today! 👫",
        "The universe ships it! 🌌💕",
    ]

    text = (
        f"<blockquote>"
        f"💑 <b>Today's Couple!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💘 {_mention(u1)}\n"
        f"    &\n"
        f"💝 {_mention(u2)}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💬 {random.choice(love_lines)}\n"
        f"📅 Couple resets tomorrow!"
        f"</blockquote>"
    )

    try:
        if gif:
            sent = await message.reply_animation(
                gif, caption=text, parse_mode=enums.ParseMode.HTML
            )
        else:
            sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
    except Exception:
        sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)

    asyncio.create_task(_auto_delete(sent, COUPLE_DELETE_DELAY))


# ── /mycouple ─────────────────────────────────────────────────────────────────

@app.on_message(filters.command("mycouple") & filters.group)
async def cmd_mycouple(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None

    if not user_id:
        return

    pair = _get_couple(chat_id)
    if not pair or user_id not in pair:
        sent = await message.reply(
            "<blockquote>💔 You don't have a couple today!\nUse /couple to get paired.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 30))
        return

    partner_id = pair[1] if pair[0] == user_id else pair[0]
    try:
        partner = await app.get_users(partner_id)
        text = (
            f"<blockquote>"
            f"💑 <b>Your Today's Couple</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💘 Your partner: {_mention(partner)}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📅 Resets tomorrow!"
            f"</blockquote>"
        )
    except Exception:
        text = (
            "<blockquote>"
            "💑 You have a couple today!\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📅 Resets tomorrow!"
            "</blockquote>"
        )

    sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_auto_delete(sent, COUPLE_DELETE_DELAY))


# ── /couplebreak ──────────────────────────────────────────────────────────────

@app.on_message(filters.command("couplebreak") & filters.group)
async def cmd_couplebreak(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None

    if not user_id:
        return

    pair = _get_couple(chat_id)
    if not pair or user_id not in pair:
        sent = await message.reply(
            "<blockquote>💔 You don't have an active couple to break.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 30))
        return

    _couples[chat_id]["pair"] = None

    sent = await message.reply(
        "<blockquote>💔 <b>Couple broken!</b>\nUse /couple to get a new one.</blockquote>",
        parse_mode=enums.ParseMode.HTML,
    )
    asyncio.create_task(_auto_delete(sent, 30))


# ── /coupletop ────────────────────────────────────────────────────────────────

@app.on_message(filters.command("coupletop") & filters.group)
async def cmd_coupletop(_, message: Message):
    chat_id = message.chat.id
    data = _couples.get(chat_id)

    if not data or not data.get("count"):
        sent = await message.reply(
            "<blockquote>📊 No couple history yet! Use /couple to start.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 30))
        return

    sorted_counts = sorted(data["count"].items(), key=lambda x: x[1], reverse=True)[:10]

    lines = ["💑 <b>Top Couples (by appearances)</b>\n━━━━━━━━━━━━━━━━━━"]
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 10

    for i, (uid, count) in enumerate(sorted_counts):
        try:
            u = await app.get_users(uid)
            name = (u.first_name or "User").replace("<", "&lt;").replace(">", "&gt;")
            display = f"<a href='tg://user?id={uid}'>{name}</a>"
        except Exception:
            display = f"<a href='tg://user?id={uid}'>User {uid}</a>"
        lines.append(f"{medals[i]} {display} — {count} time{'s' if count != 1 else ''}")

    text = "<blockquote>" + "\n".join(lines) + "</blockquote>"
    sent = await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    asyncio.create_task(_auto_delete(sent, COUPLE_DELETE_DELAY))
