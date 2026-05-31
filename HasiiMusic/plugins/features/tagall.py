"""
TagAll Plugin — v5 FINAL (All English)
Place at: HasiiMusic/plugins/features/tagall.py

Commands (admin only):
  /tagall [msg]     - Tag all members
  /tagadmins [msg]  - Tag only admins
  /stoptag          - Stop running tag session
  /gmtag [msg]      - Good Morning tag
  /gntag [msg]      - Good Night tag
  /gdtag [msg]      - Good Afternoon tag
  /gevtag [msg]     - Good Evening tag
  /gbdtag @user     - Birthday tag
  /roasttag [@user] - Roast tag (mass or single)

Note: Bot must be admin with Add Members permission.
Auto-delete: All messages deleted after 24 hours.
"""

import asyncio
import random
import re

from pyrogram import enums, filters, types
from HasiiMusic import app
from HasiiMusic.helpers.gif_manager import get_random_gif, register_gif_commands

_active_tags: dict[int, bool] = {}
TAG_DELETE_DELAY = 86400

for _gtype, _prefix in [("gmtag", "gm"), ("gntag", "gn"), ("gdtag", "gd"), ("gevtag", "gev"), ("gbdtag", "gbd")]:
    try:
        register_gif_commands(app, _gtype, _prefix)
    except Exception:
        pass

ROAST_LINES = [
    "🔥 Wake up! Even your WiFi has a better connection than your brain.",
    "😂 The group IQ drops every time you speak. Congrats on the achievement.",
    "🤡 You're living proof that evolution can go in reverse.",
    "💀 Your village called — they want their idiot back immediately.",
    "🗑️ Scientists discovered a new dimension of uselessness — and named it after you.",
    "😴 You're not lazy, you're just on permanent energy-saving mode.",
    "🧠 Your brain has more buffering time than a 2G connection.",
    "🐢 Even your excuses are slow.",
    "📵 Your presence in this group is like airplane mode — totally disconnected from reality.",
    "🤦 The fact that you exist is already a spoiler for natural selection.",
    "🎭 You have the personality of a loading screen with no progress bar.",
    "🏆 Congratulations! You've won the award for most spectacularly average existence.",
    "📉 Your IQ called — it wants more digits. Negative ones.",
    "🌚 You're the human version of a Monday morning in the rain.",
    "🎪 You're proof that even clowns need a support group sometimes.",
    "🪞 The mirror winces when you look in it — even it has standards.",
    "📚 You studied hard to become this confused — respect the dedication.",
    "🔋 You drain everyone's energy just by existing — truly a talent.",
]

ROAST_HEADERS = [
    "🔥 <b>ROAST SESSION ACTIVATED! 🔥</b>\nNobody is safe. Brace yourselves! 😈",
    "💀 <b>The Roast Train Has Arrived! 🚂</b>\nAll aboard the express to roast city! 🎭",
    "😂 <b>ATTENTION EVERYONE!</b>\nA mass roast is in progress. Maintain your dignity — if you have any. 🤡",
    "🔥 <b>Roast Alert! 🚨</b>\nEveryone is getting cooked today. No exceptions! 🍳",
    "🎯 <b>Mass Roast Incoming!</b>\nPrepare your feelings — they won't survive what's coming. 💀",
]


def _mention(user) -> str:
    name = (user.first_name or "User").replace("<", "&lt;").replace(">", "&gt;")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"


async def _is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


async def _auto_delete(msg, delay: int = TAG_DELETE_DELAY):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


async def _safe_send(chat_id: int, text: str, sent_msgs: list, **kwargs):
    try:
        msg = await app.send_message(
            chat_id, text,
            disable_notification=True,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
            **kwargs
        )
        sent_msgs.append(msg)
    except Exception:
        pass


def _extract_url(text: str) -> str:
    match = re.search(r'https?://\S+', text)
    return match.group(0) if match else ""


async def _do_tagall(
    chat_id: int,
    trigger_user,
    custom_msg: str,
    gif_type: str = None,
    chunk_size: int = 5,
    delay: float = 1.5,
    roast_mode: bool = False,
):
    members = []
    try:
        async for m in app.get_chat_members(chat_id):
            if m.user and not m.user.is_bot and not m.user.is_deleted:
                members.append(m.user)
    except Exception as e:
        err = await app.send_message(
            chat_id,
            f"<blockquote>❌ <b>Failed to fetch members!</b>\n\nMake sure the bot is an admin with Add Members permission.\n<code>{e}</code></blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
        asyncio.create_task(_auto_delete(err, TAG_DELETE_DELAY))
        return

    if not members:
        msg = await app.send_message(chat_id, "<blockquote>❌ No members found to tag.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(msg, TAG_DELETE_DELAY))
        return

    _active_tags[chat_id] = True
    sent_msgs = []

    url = _extract_url(custom_msg)
    url_line = f"\n🔗 <a href='{url}'>Open Link</a>" if url else ""
    trigger_line = f"📢 <b>Tagged by:</b> {_mention(trigger_user)}" if trigger_user else "📢 <b>Group Tag</b>"

    header_text = (
        f"<blockquote>"
        f"{trigger_line}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Message:</b>\n{custom_msg}"
        f"{url_line}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Tagging:</b> {len(members)} members"
        f"</blockquote>"
    )

    header_sent = None
    if gif_type:
        gif = get_random_gif(gif_type)
        if gif:
            try:
                header_sent = await app.send_animation(
                    chat_id, gif, caption=header_text,
                    parse_mode=enums.ParseMode.HTML, disable_notification=True,
                )
                sent_msgs.append(header_sent)
            except Exception:
                pass

    if not header_sent:
        try:
            h = await app.send_message(chat_id, header_text, disable_notification=True, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
            sent_msgs.append(h)
        except Exception:
            pass

    await asyncio.sleep(0.8)

    for i in range(0, len(members), chunk_size):
        if not _active_tags.get(chat_id):
            break
        chunk = members[i: i + chunk_size]
        if roast_mode:
            mentions = " ".join(_mention(u) for u in chunk)
            roast = random.choice(ROAST_LINES)
            text = f"{mentions}\n<i>{roast}</i>"
        else:
            text = " ".join(_mention(u) for u in chunk)
        await _safe_send(chat_id, text, sent_msgs)
        await asyncio.sleep(delay)

    _active_tags.pop(chat_id, None)

    for msg in sent_msgs:
        asyncio.create_task(_auto_delete(msg, TAG_DELETE_DELAY))


# ── /tagall ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("tagall") & filters.group)
async def cmd_tagall(_, message: types.Message):
    if not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply(
            "<blockquote>🚫 Only admins can use /tagall.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 10))
        return

    if _active_tags.get(message.chat.id):
        sent = await message.reply(
            "<blockquote>⚠️ A tag session is already running! Use /stoptag to stop it.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 15))
        return

    custom_msg = " ".join(message.command[1:]).strip() or "👋 Hello everyone!"
    asyncio.create_task(
        _do_tagall(message.chat.id, message.from_user, custom_msg, gif_type="tagall")
    )

    try:
        await message.delete()
    except Exception:
        pass


# ── /tagadmins ────────────────────────────────────────────────────────────────

@app.on_message(filters.command("tagadmins") & filters.group)
async def cmd_tagadmins(_, message: types.Message):
    if not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply(
            "<blockquote>🚫 Only admins can use /tagadmins.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 10))
        return

    chat_id = message.chat.id
    custom_msg = " ".join(message.command[1:]).strip() or "📢 Attention admins!"

    admins = []
    try:
        async for m in app.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if m.user and not m.user.is_bot:
                admins.append(m.user)
    except Exception as e:
        sent = await message.reply(
            f"<blockquote>❌ Failed to fetch admins!\n<code>{e}</code></blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 30))
        return

    if not admins:
        sent = await message.reply(
            "<blockquote>❌ No admins found.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 15))
        return

    trigger_line = f"📢 <b>Tagged by:</b> {_mention(message.from_user)}"
    header_text = (
        f"<blockquote>"
        f"{trigger_line}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Message:</b>\n{custom_msg}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👮 <b>Tagging:</b> {len(admins)} admin(s)"
        f"</blockquote>"
    )

    sent_msgs = []
    try:
        gif = get_random_gif("tagadmins")
        if gif:
            h = await app.send_animation(chat_id, gif, caption=header_text, parse_mode=enums.ParseMode.HTML, disable_notification=True)
        else:
            h = await app.send_message(chat_id, header_text, parse_mode=enums.ParseMode.HTML, disable_notification=True)
        sent_msgs.append(h)
    except Exception:
        pass

    mentions = " ".join(_mention(u) for u in admins)
    await _safe_send(chat_id, mentions, sent_msgs)

    for msg in sent_msgs:
        asyncio.create_task(_auto_delete(msg, TAG_DELETE_DELAY))

    try:
        await message.delete()
    except Exception:
        pass


# ── /stoptag ──────────────────────────────────────────────────────────────────

@app.on_message(filters.command("stoptag") & filters.group)
async def cmd_stoptag(_, message: types.Message):
    if not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply(
            "<blockquote>🚫 Only admins can use /stoptag.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 10))
        return

    chat_id = message.chat.id
    if _active_tags.get(chat_id):
        _active_tags[chat_id] = False
        sent = await message.reply(
            "<blockquote>🛑 <b>Tag session stopped!</b></blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
    else:
        sent = await message.reply(
            "<blockquote>ℹ️ No active tag session in this group.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )

    asyncio.create_task(_auto_delete(sent, 15))

    try:
        await message.delete()
    except Exception:
        pass


# ── /roasttag ─────────────────────────────────────────────────────────────────

@app.on_message(filters.command("roasttag") & filters.group)
async def cmd_roasttag(_, message: types.Message):
    if not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply(
            "<blockquote>🚫 Only admins can use /roasttag.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 10))
        return

    if _active_tags.get(message.chat.id):
        sent = await message.reply(
            "<blockquote>⚠️ A tag session is already running! Use /stoptag first.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, 15))
        return

    chat_id = message.chat.id

    # Single-user roast if @username or reply
    target_user = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        raw = message.command[1].lstrip("@")
        try:
            target_user = await app.get_users(raw)
        except Exception:
            pass

    if target_user:
        # Single roast
        roast = random.choice(ROAST_LINES)
        text = (
            f"<blockquote>"
            f"🔥 <b>Roast Time!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎯 {_mention(target_user)}\n"
            f"<i>{roast}</i>"
            f"</blockquote>"
        )
        sent = await message.reply(text, parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(sent, TAG_DELETE_DELAY))
    else:
        # Mass roast
        header = random.choice(ROAST_HEADERS)
        asyncio.create_task(
            _do_tagall(chat_id, message.from_user, header, gif_type="roasttag", roast_mode=True)
        )

    try:
        await message.delete()
    except Exception:
        pass


# ── /gmtag ────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("gmtag") & filters.group)
async def cmd_gmtag(_, message: types.Message):
    if not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(sent, 10))
        return
    if _active_tags.get(message.chat.id):
        sent = await message.reply("<blockquote>⚠️ Tag already running! /stoptag first.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(sent, 15))
        return

    extra = " ".join(message.command[1:]).strip()
    gm_msg = f"🌅 <b>Good Morning Everyone!</b> ☀️" + (f"\n{extra}" if extra else "")
    asyncio.create_task(_do_tagall(message.chat.id, message.from_user, gm_msg, gif_type="gmtag"))
    try:
        await message.delete()
    except Exception:
        pass


# ── /gntag ────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("gntag") & filters.group)
async def cmd_gntag(_, message: types.Message):
    if not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(sent, 10))
        return
    if _active_tags.get(message.chat.id):
        sent = await message.reply("<blockquote>⚠️ Tag already running! /stoptag first.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(sent, 15))
        return

    extra = " ".join(message.command[1:]).strip()
    gn_msg = f"🌙 <b>Good Night Everyone!</b> 😴⭐" + (f"\n{extra}" if extra else "")
    asyncio.create_task(_do_tagall(message.chat.id, message.from_user, gn_msg, gif_type="gntag"))
    try:
        await message.delete()
    except Exception:
        pass


# ── /gdtag ────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("gdtag") & filters.group)
async def cmd_gdtag(_, message: types.Message):
    if not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(sent, 10))
        return
    if _active_tags.get(message.chat.id):
        sent = await message.reply("<blockquote>⚠️ Tag already running! /stoptag first.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(sent, 15))
        return

    extra = " ".join(message.command[1:]).strip()
    gd_msg = f"☀️ <b>Good Afternoon Everyone!</b> 🌤️" + (f"\n{extra}" if extra else "")
    asyncio.create_task(_do_tagall(message.chat.id, message.from_user, gd_msg, gif_type="gdtag"))
    try:
        await message.delete()
    except Exception:
        pass


# ── /gevtag ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("gevtag") & filters.group)
async def cmd_gevtag(_, message: types.Message):
    if not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(sent, 10))
        return
    if _active_tags.get(message.chat.id):
        sent = await message.reply("<blockquote>⚠️ Tag already running! /stoptag first.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(sent, 15))
        return

    extra = " ".join(message.command[1:]).strip()
    gev_msg = f"🌆 <b>Good Evening Everyone!</b> 🌇" + (f"\n{extra}" if extra else "")
    asyncio.create_task(_do_tagall(message.chat.id, message.from_user, gev_msg, gif_type="gevtag"))
    try:
        await message.delete()
    except Exception:
        pass


# ── /gbdtag ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("gbdtag") & filters.group)
async def cmd_gbdtag(_, message: types.Message):
    if not await _is_admin(message.chat.id, message.from_user.id):
        sent = await message.reply("<blockquote>🚫 Admins only.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(sent, 10))
        return

    chat_id = message.chat.id
    target_user = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        raw = message.command[1].lstrip("@")
        try:
            target_user = await app.get_users(raw)
        except Exception:
            pass

    bday_person = _mention(target_user) if target_user else "Someone special 🎂"

    if _active_tags.get(chat_id):
        sent = await message.reply("<blockquote>⚠️ Tag already running! /stoptag first.</blockquote>", parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(_auto_delete(sent, 15))
        return

    gbd_msg = (
        f"🎂 <b>HAPPY BIRTHDAY!</b> 🎉\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎁 It's {bday_person}'s birthday!\n"
        f"🥳 Everyone wish them!"
    )
    asyncio.create_task(_do_tagall(chat_id, message.from_user, gbd_msg, gif_type="gbdtag"))
    try:
        await message.delete()
    except Exception:
        pass
