"""
TagAll Plugin — v6 FIXED
Place at: HasiiMusic/plugins/features/tagall.py

Commands (admin only):
  /tagall [msg]     - Tag all members
  /tagadmins [msg]  - Tag only admins
  /stoptag          - Stop running tag
  /gmtag [msg]      - Good Morning tag
  /gntag [msg]      - Good Night tag
  /gdtag [msg]      - Good Afternoon tag
  /gevtag [msg]     - Good Evening tag
  /roasttag [@user] - Roast tag

Note: Bot must be admin with Add Members permission.
"""

import asyncio
import random

from pyrogram import enums, filters
from pyrogram.types import Message

from HasiiMusic import app
from HasiiMusic.helpers.gif_manager import get_random_gif

_active: dict[int, bool] = {}
_DEL = 86400

ROAST_LINES = [
    "🔥 Even your WiFi has a better connection than your brain.",
    "😂 The group IQ drops every time you speak.",
    "🤡 You're living proof that evolution can go in reverse.",
    "💀 Your village called — they want their idiot back.",
    "😴 You're not lazy, you're just on permanent energy-saving mode.",
    "🧠 Your brain has more buffering time than a 2G connection.",
    "📵 Your presence is like airplane mode — totally disconnected.",
    "🎭 You have the personality of a loading screen with no progress bar.",
    "📉 Your IQ called — it wants more digits. Negative ones.",
    "🔋 You drain everyone's energy just by existing — truly a talent.",
]


def _mention(user) -> str:
    name = (user.first_name or "User").replace("<", "&lt;").replace(">", "&gt;")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"


async def _is_admin(chat_id: int, user_id: int) -> bool:
    try:
        m = await app.get_chat_member(chat_id, user_id)
        return m.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)
    except Exception:
        return False


async def _del(msg, delay=_DEL):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


async def _fetch_members(chat_id: int) -> list:
    members = []
    try:
        async for m in app.get_chat_members(chat_id):
            if m.user and not m.user.is_bot and not m.user.is_deleted:
                members.append(m.user)
    except Exception:
        pass
    return members


async def _run_tag(chat_id, trigger, header, members, gif_type=None, roast=False, chunk=5, delay=1.5):
    _active[chat_id] = True
    sent_msgs = []

    gif = get_random_gif(gif_type) if gif_type else None
    try:
        if gif:
            h = await app.send_animation(chat_id, gif, caption=header, parse_mode=enums.ParseMode.HTML, disable_notification=True)
        else:
            h = await app.send_message(chat_id, header, parse_mode=enums.ParseMode.HTML, disable_notification=True, disable_web_page_preview=True)
        sent_msgs.append(h)
    except Exception:
        pass

    await asyncio.sleep(0.5)

    for i in range(0, len(members), chunk):
        if not _active.get(chat_id):
            break
        group = members[i: i + chunk]
        if roast:
            text = " ".join(_mention(u) for u in group) + f"\n<i>{random.choice(ROAST_LINES)}</i>"
        else:
            text = " ".join(_mention(u) for u in group)
        try:
            msg = await app.send_message(chat_id, text, parse_mode=enums.ParseMode.HTML, disable_notification=True, disable_web_page_preview=True)
            sent_msgs.append(msg)
        except Exception:
            pass
        await asyncio.sleep(delay)

    _active.pop(chat_id, None)
    for m in sent_msgs:
        asyncio.create_task(_del(m, _DEL))


# ── /tagall ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("tagall") & filters.group)
async def cmd_tagall(_, message: Message):
    chat_id = message.chat.id
    if not message.from_user or not await _is_admin(chat_id, message.from_user.id):
        s = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return
    if _active.get(chat_id):
        s = await message.reply("<blockquote>⚠️ Tag running! /stoptag first.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return

    members = await _fetch_members(chat_id)
    if not members:
        s = await message.reply(
            "<blockquote>❌ No members found!\nMake sure I'm admin with <b>Add Members</b> permission.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_del(s, 20))
        return

    msg_text = " ".join(message.command[1:]).strip() or "👋 Hello everyone!"
    header = (
        f"<blockquote>📢 <b>Tagged by:</b> {_mention(message.from_user)}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 {msg_text}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 Tagging <b>{len(members)}</b> members</blockquote>"
    )
    asyncio.create_task(_run_tag(chat_id, message.from_user, header, members, gif_type="tagall"))
    try:
        await message.delete()
    except Exception:
        pass


# ── /tagadmins ────────────────────────────────────────────────────────────────

@app.on_message(filters.command("tagadmins") & filters.group)
async def cmd_tagadmins(_, message: Message):
    chat_id = message.chat.id
    if not message.from_user or not await _is_admin(chat_id, message.from_user.id):
        s = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return

    admins = []
    try:
        async for m in app.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if m.user and not m.user.is_bot:
                admins.append(m.user)
    except Exception as e:
        s = await message.reply(f"<blockquote>❌ Failed!\n<code>{e}</code></blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 20))
        return

    if not admins:
        s = await message.reply("<blockquote>❌ No admins found.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return

    msg_text = " ".join(message.command[1:]).strip() or "📢 Attention admins!"
    header = (
        f"<blockquote>👮 <b>Admin Tag by:</b> {_mention(message.from_user)}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 {msg_text}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 Tagging <b>{len(admins)}</b> admin(s)</blockquote>"
    )
    sent = []
    gif = get_random_gif("tagadmins")
    try:
        h = await app.send_animation(chat_id, gif, caption=header, parse_mode=enums.ParseMode.HTML, disable_notification=True) if gif else await app.send_message(chat_id, header, parse_mode=enums.ParseMode.HTML, disable_notification=True)
        sent.append(h)
    except Exception:
        pass
    try:
        m = await app.send_message(chat_id, " ".join(_mention(u) for u in admins), parse_mode=enums.ParseMode.HTML, disable_notification=True)
        sent.append(m)
    except Exception:
        pass

    for msg in sent:
        asyncio.create_task(_del(msg, _DEL))
    try:
        await message.delete()
    except Exception:
        pass


# ── /stoptag ──────────────────────────────────────────────────────────────────

@app.on_message(filters.command("stoptag") & filters.group)
async def cmd_stoptag(_, message: Message):
    chat_id = message.chat.id
    if not message.from_user or not await _is_admin(chat_id, message.from_user.id):
        s = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return

    if _active.get(chat_id):
        _active[chat_id] = False
        s = await message.reply("<blockquote>🛑 Tag stopped!</blockquote>", parse_mode=enums.ParseMode.HTML)
    else:
        s = await message.reply("<blockquote>ℹ️ No active tag session.</blockquote>", parse_mode=enums.ParseMode.HTML)
    asyncio.create_task(_del(s, 10))
    try:
        await message.delete()
    except Exception:
        pass


# ── /roasttag ─────────────────────────────────────────────────────────────────

@app.on_message(filters.command("roasttag") & filters.group)
async def cmd_roasttag(_, message: Message):
    chat_id = message.chat.id
    if not message.from_user or not await _is_admin(chat_id, message.from_user.id):
        s = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return
    if _active.get(chat_id):
        s = await message.reply("<blockquote>⚠️ Tag running! /stoptag first.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return

    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await app.get_users(message.command[1].lstrip("@"))
        except Exception:
            pass

    if target:
        s = await message.reply(
            f"<blockquote>🔥 <b>Roast!</b>\n━━━━━━━━━━━━━━━━━━\n🎯 {_mention(target)}\n<i>{random.choice(ROAST_LINES)}</i></blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_del(s, _DEL))
    else:
        members = await _fetch_members(chat_id)
        if not members:
            s = await message.reply(
                "<blockquote>❌ No members found! Make sure I'm admin with Add Members permission.</blockquote>",
                parse_mode=enums.ParseMode.HTML,
            )
            asyncio.create_task(_del(s, 20))
            return
        header = (
            f"<blockquote>🔥 <b>MASS ROAST!</b> 😈\n━━━━━━━━━━━━━━━━━━\n"
            f"Nobody is safe!\n👥 Roasting <b>{len(members)}</b> members</blockquote>"
        )
        asyncio.create_task(_run_tag(chat_id, message.from_user, header, members, gif_type="roasttag", roast=True))
    try:
        await message.delete()
    except Exception:
        pass


# ── Time-based tags ───────────────────────────────────────────────────────────

async def _time_tag(message: Message, greeting: str, gif_type: str):
    chat_id = message.chat.id
    if not message.from_user or not await _is_admin(chat_id, message.from_user.id):
        s = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return
    if _active.get(chat_id):
        s = await message.reply("<blockquote>⚠️ Tag running! /stoptag first.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 10))
        return

    members = await _fetch_members(chat_id)
    if not members:
        s = await message.reply(
            "<blockquote>❌ No members found! Make sure I'm admin with Add Members permission.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_del(s, 20))
        return

    extra = " ".join(message.command[1:]).strip()
    header = (
        f"<blockquote>{greeting}" +
        (f"\n{extra}" if extra else "") +
        f"\n━━━━━━━━━━━━━━━━━━\n👥 Tagging <b>{len(members)}</b> members</blockquote>"
    )
    asyncio.create_task(_run_tag(chat_id, message.from_user, header, members, gif_type=gif_type))
    try:
        await message.delete()
    except Exception:
        pass


@app.on_message(filters.command("gmtag") & filters.group)
async def cmd_gmtag(_, message: Message):
    await _time_tag(message, "🌅 <b>Good Morning Everyone!</b> ☀️", "gmtag")


@app.on_message(filters.command("gntag") & filters.group)
async def cmd_gntag(_, message: Message):
    await _time_tag(message, "🌙 <b>Good Night Everyone!</b> 😴⭐", "gntag")


@app.on_message(filters.command("gdtag") & filters.group)
async def cmd_gdtag(_, message: Message):
    await _time_tag(message, "☀️ <b>Good Afternoon Everyone!</b> 🌤️", "gdtag")


@app.on_message(filters.command("gevtag") & filters.group)
async def cmd_gevtag(_, message: Message):
    await _time_tag(message, "🌆 <b>Good Evening Everyone!</b> 🌇", "gevtag")
