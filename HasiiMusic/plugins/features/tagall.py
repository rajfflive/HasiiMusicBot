"""
TagAll Plugin — v7 PREMIUM
Place at: HasiiMusic/plugins/features/tagall.py
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
    "🤡 Living proof that evolution can go in reverse.",
    "💀 Your village called — they want their idiot back.",
    "😴 Not lazy, just on permanent energy-saving mode.",
    "🧠 More buffering time than a 2G connection.",
    "📵 Your presence is like airplane mode — totally disconnected.",
    "📉 Your IQ called — it wants more digits. Negative ones.",
    "🔋 You drain everyone's energy just by existing.",
]

QUOTES = [
    "Together we achieve more than alone.",
    "A group that talks together, stays together.",
    "Every voice matters — especially yours.",
    "Great things happen when great people unite.",
    "One message, infinite reach.",
    "The strongest signal is a group in sync.",
    "Your presence makes this group complete.",
    "Attention is the rarest form of generosity.",
]


def _mention(user) -> str:
    name = (user.first_name or "User").replace("<", "&lt;").replace(">", "&gt;")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"


def _name(user) -> str:
    return (user.first_name or "User").replace("<", "&lt;").replace(">", "&gt;")


async def _is_admin(chat_id, user_id) -> bool:
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


async def _fetch_members(chat_id) -> list:
    members = []
    try:
        async for m in app.get_chat_members(chat_id):
            if m.user and not m.user.is_bot and not m.user.is_deleted:
                members.append(m.user)
    except Exception:
        pass
    return members


def _build_header(trigger, msg_text: str, total: int, title: str = "📣 Group Announcement") -> str:
    return (
        f"<blockquote>"
        f"┌─────────────────────\n"
        f"│  {title}\n"
        f"└─────────────────────\n"
        f"\n"
        f"👤 <b>From:</b> {_mention(trigger)}\n"
        f"\n"
        f"💬 <b>Message:</b>\n"
        f"❝ {msg_text} ❞\n"
        f"\n"
        f"✦ <i>{random.choice(QUOTES)}</i>\n"
        f"\n"
        f"─────────────────────\n"
        f"👥 Tagging <b>{total}</b> members"
        f"</blockquote>"
    )


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
        text = " ".join(_mention(u) for u in group)
        if roast:
            text += f"\n<i>{random.choice(ROAST_LINES)}</i>"
        try:
            msg = await app.send_message(chat_id, text, parse_mode=enums.ParseMode.HTML, disable_notification=True, disable_web_page_preview=True)
            sent_msgs.append(msg)
        except Exception:
            pass
        await asyncio.sleep(delay)
    _active.pop(chat_id, None)
    for m in sent_msgs:
        asyncio.create_task(_del(m, _DEL))


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
        s = await message.reply("<blockquote>❌ No members found!\nMake sure I'm admin with <b>Add Members</b> permission.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 20))
        return
    msg_text = " ".join(message.command[1:]).strip() or "Attention everyone! 🔔"
    header = _build_header(message.from_user, msg_text, len(members), "📣 Group Announcement")
    asyncio.create_task(_run_tag(chat_id, message.from_user, header, members, gif_type="tagall"))
    try:
        await message.delete()
    except Exception:
        pass


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
    msg_text = " ".join(message.command[1:]).strip() or "Admins, attention please! 👮"
    header = _build_header(message.from_user, msg_text, len(admins), "👮 Admin Ping")
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
        text = (
            f"<blockquote>"
            f"┌─────────────────────\n"
            f"│  🔥 Roast Session!\n"
            f"└─────────────────────\n\n"
            f"🎯 <b>Target:</b> {_mention(target)}\n\n"
            f"💬 <i>{random.choice(ROAST_LINES)}</i>\n\n"
            f"─────────────────────\n"
            f"🔥 Served by {_mention(message.from_user)}"
            f"</blockquote>"
        )
        s = await message.reply(text, parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, _DEL))
    else:
        members = await _fetch_members(chat_id)
        if not members:
            s = await message.reply("<blockquote>❌ No members! Make sure I'm admin with Add Members permission.</blockquote>", parse_mode=enums.ParseMode.HTML)
            asyncio.create_task(_del(s, 20))
            return
        header = (
            f"<blockquote>"
            f"┌─────────────────────\n"
            f"│  🔥 MASS ROAST!\n"
            f"└─────────────────────\n\n"
            f"😈 <b>Roast master:</b> {_mention(message.from_user)}\n\n"
            f"💀 <i>Nobody is safe. Brace yourselves.</i>\n\n"
            f"─────────────────────\n"
            f"👥 Roasting <b>{len(members)}</b> members"
            f"</blockquote>"
        )
        asyncio.create_task(_run_tag(chat_id, message.from_user, header, members, gif_type="roasttag", roast=True))
    try:
        await message.delete()
    except Exception:
        pass


async def _time_tag(message: Message, emoji: str, greeting: str, sub: str, gif_type: str):
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
        s = await message.reply("<blockquote>❌ No members! Make sure I'm admin with Add Members permission.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_del(s, 20))
        return
    extra = " ".join(message.command[1:]).strip()
    msg_text = extra if extra else sub
    header = _build_header(message.from_user, f"{emoji} {greeting} {msg_text}", len(members), f"{emoji} {greeting}")
    asyncio.create_task(_run_tag(chat_id, message.from_user, header, members, gif_type=gif_type))
    try:
        await message.delete()
    except Exception:
        pass


@app.on_message(filters.command("gmtag") & filters.group)
async def cmd_gmtag(_, message: Message):
    await _time_tag(message, "🌅", "Good Morning!", "Rise & shine ☀️", "gmtag")

@app.on_message(filters.command("gntag") & filters.group)
async def cmd_gntag(_, message: Message):
    await _time_tag(message, "🌙", "Good Night!", "Sweet dreams 😴⭐", "gntag")

@app.on_message(filters.command("gdtag") & filters.group)
async def cmd_gdtag(_, message: Message):
    await _time_tag(message, "☀️", "Good Afternoon!", "Hope your day is great 🌤️", "gdtag")

@app.on_message(filters.command("gevtag") & filters.group)
async def cmd_gevtag(_, message: Message):
    await _time_tag(message, "🌆", "Good Evening!", "Relax & unwind 🌇", "gevtag")
