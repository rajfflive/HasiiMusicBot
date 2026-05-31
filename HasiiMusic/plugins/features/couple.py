"""
Couple Plugin — v4 FIXED
Place at: HasiiMusic/plugins/features/couple.py

Commands:
  /couple / /couples  - Get today's random couple
  /mycouple           - Check your partner
  /couplebreak        - Break your pairing
"""

import asyncio
import random
from datetime import date

from pyrogram import enums, filters
from pyrogram.types import Message

from HasiiMusic import app
from HasiiMusic.helpers.gif_manager import get_random_gif

_couples: dict[int, dict] = {}

LOVE_LINES = [
    "A match written in the stars! 🌟",
    "Love is in the air! 💨❤️",
    "The algorithm has spoken! 🤖💘",
    "Destiny brought them together! 🔮",
    "Chemistry detected! 🧪❤️",
    "Soulmates for today! 👫",
    "The universe ships it! 🌌💕",
]


def _today() -> str:
    return date.today().isoformat()


def _get_pair(chat_id: int):
    d = _couples.get(chat_id)
    if not d or d["date"] != _today():
        _couples[chat_id] = {"date": _today(), "pair": None}
        return None
    return d["pair"]


def _set_pair(chat_id: int, uid1: int, uid2: int):
    _couples[chat_id] = {"date": _today(), "pair": (uid1, uid2)}


def _mention(user) -> str:
    name = (user.first_name or "User").replace("<", "&lt;").replace(">", "&gt;")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"


async def _del(msg, delay=86400):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


async def _do_couple(message: Message):
    chat_id = message.chat.id

    pair = _get_pair(chat_id)
    if pair:
        try:
            u1 = await app.get_users(pair[0])
            u2 = await app.get_users(pair[1])
        except Exception:
            _couples[chat_id]["pair"] = None
            await _do_couple(message)
            return

        gif = get_random_gif("couple")
        text = (
            "<blockquote>"
            "💑 <b>Today's Couple is Already Set!</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"💘 {_mention(u1)}\n"
            f"💝 {_mention(u2)}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "❤️ Come back tomorrow for a new couple!"
            "</blockquote>"
        )
        try:
            if gif:
                sent = await message.reply_animation(gif, caption=text, parse_mode=enums.ParseMode.HTML)
            else:
                sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
        except Exception:
            sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(sent))
        return

    # Fetch members
    members = []
    try:
        async for m in app.get_chat_members(chat_id):
            if m.user and not m.user.is_bot and not m.user.is_deleted:
                members.append(m.user)
    except Exception as e:
        sent = await message.reply(
            f"<blockquote>❌ <b>Couldn't fetch members!</b>\nMake sure I'm admin with Add Members permission.\n<code>{e}</code></blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_del(sent, 30))
        return

    if len(members) < 2:
        sent = await message.reply(
            "<blockquote>❌ Need at least 2 members to make a couple!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_del(sent, 20))
        return

    u1, u2 = random.sample(members, 2)
    _set_pair(chat_id, u1.id, u2.id)

    gif = get_random_gif("couple")
    text = (
        "<blockquote>"
        "💑 <b>Today's Couple!</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💘 {_mention(u1)}\n"
        "    &\n"
        f"💝 {_mention(u2)}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💬 {random.choice(LOVE_LINES)}\n"
        "📅 Resets tomorrow!"
        "</blockquote>"
    )

    try:
        if gif:
            sent = await message.reply_animation(gif, caption=text, parse_mode=enums.ParseMode.HTML)
        else:
            sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
    except Exception:
        sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)

    asyncio.create_task(_del(sent))


# ── /couple AND /couples ──────────────────────────────────────────────────────

@app.on_message(filters.command(["couple", "couples"]) & filters.group)
async def cmd_couple(_, message: Message):
    await _do_couple(message)


# ── /mycouple ─────────────────────────────────────────────────────────────────

@app.on_message(filters.command("mycouple") & filters.group)
async def cmd_mycouple(_, message: Message):
    if not message.from_user:
        return

    pair = _get_pair(message.chat.id)
    if not pair or message.from_user.id not in pair:
        sent = await message.reply(
            "<blockquote>💔 You have no couple today!\nUse /couple to get paired.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_del(sent, 20))
        return

    partner_id = pair[1] if pair[0] == message.from_user.id else pair[0]
    try:
        partner = await app.get_users(partner_id)
        text = (
            "<blockquote>"
            "💑 <b>Your Couple Today</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"💘 Partner: {_mention(partner)}\n"
            "📅 Resets tomorrow!"
            "</blockquote>"
        )
    except Exception:
        text = "<blockquote>💑 You have a couple today! 📅 Resets tomorrow!</blockquote>"

    sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_del(sent))


# ── /couplebreak ──────────────────────────────────────────────────────────────

@app.on_message(filters.command("couplebreak") & filters.group)
async def cmd_couplebreak(_, message: Message):
    if not message.from_user:
        return

    pair = _get_pair(message.chat.id)
    if not pair or message.from_user.id not in pair:
        sent = await message.reply(
            "<blockquote>💔 No active couple to break.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_del(sent, 20))
        return

    _couples[message.chat.id]["pair"] = None
    sent = await message.reply(
        "<blockquote>💔 <b>Couple broken!</b> Use /couple to get a new one.</blockquote>",
        parse_mode=enums.ParseMode.HTML,
    )
    asyncio.create_task(_del(sent, 20))
