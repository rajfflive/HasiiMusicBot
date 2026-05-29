"""
TagAll Plugin — v2
Commands:
  /tagall [msg]    - Tag all members, one per line with gap, shows who triggered
  /tagadmins [msg] - Tag only admins
  /stoptag         - Stop active tagging
  /gmtag [msg]     - Good Morning tag
  /gntag [msg]     - Good Night tag
  /gdtag [msg]     - Good Afternoon tag
  /gevtag [msg]    - Good Evening tag
  /gbdtag @user    - Birthday tag for someone
"""

import asyncio
from pyrogram import enums, filters, types
from HasiiMusic import app

_active_tags: dict[int, bool] = {}


async def _is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


def _mention(user) -> str:
    return f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"


async def _do_tagall(chat_id: int, trigger_user, header_text: str, chunk_size: int = 4, delay: float = 1.5):
    members = []
    try:
        async for m in app.get_chat_members(chat_id):
            if m.user.is_bot or m.user.is_deleted:
                continue
            members.append(m.user)
    except Exception as e:
        await app.send_message(
            chat_id,
            f"<blockquote>❌ Error: {e}</blockquote>",
            parse_mode="html"
        )
        return

    if not members:
        await app.send_message(
            chat_id,
            "<blockquote>❌ Koi member nahi mila.</blockquote>",
            parse_mode="html"
        )
        return

    _active_tags[chat_id] = True

    trigger_line = f"📢 <b>{_mention(trigger_user)}</b> ne tag kiya:" if trigger_user else "📢 Tag:"
    await app.send_message(
        chat_id,
        f"<blockquote>{trigger_line}\n{header_text}</blockquote>",
        disable_notification=True,
        disable_web_page_preview=True,
        parse_mode="html"
    )
    await asyncio.sleep(0.8)

    for i in range(0, len(members), chunk_size):
        if not _active_tags.get(chat_id):
            break
        chunk = members[i: i + chunk_size]
        lines = []
        for u in chunk:
            lines.append(_mention(u))
            lines.append("")
        try:
            await app.send_message(
                chat_id, "\n".join(lines).strip(),
                disable_notification=True,
                disable_web_page_preview=True,
                parse_mode="html"
            )
        except Exception:
            pass
        await asyncio.sleep(delay)

    _active_tags.pop(chat_id, None)


# ─── /stoptag ────────────────────────────────────────────────────────────────
@app.on_message(filters.command("stoptag") & filters.group)
async def stoptag_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        return
    if _active_tags.get(message.chat.id):
        _active_tags[message.chat.id] = False
        await app.send_message(
            message.chat.id,
            "<blockquote>🛑 <b>Tag stopped.</b></blockquote>",
            parse_mode="html"
        )
    else:
        await message.reply_text(
            "<blockquote>ℹ️ Koi active tag nahi hai.</blockquote>",
            parse_mode="html"
        )


# ─── /tagall ─────────────────────────────────────────────────────────────────
@app.on_message(filters.command("tagall") & filters.group)
async def tagall_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user:
        return
    if not await _is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text(
            "<blockquote>❌ Sirf admins /tagall use kar sakte hain.</blockquote>",
            parse_mode="html"
        )
    if _active_tags.get(message.chat.id):
        return await message.reply_text(
            "<blockquote>⚠️ Pehle se tag chal raha hai. /stoptag karo.</blockquote>",
            parse_mode="html"
        )

    custom_msg = " ".join(message.command[1:]) if len(message.command) > 1 else "Sabko tag kar raha hun!"
    asyncio.create_task(_do_tagall(message.chat.id, message.from_user, f"📣 {custom_msg}"))


# ─── /tagadmins ──────────────────────────────────────────────────────────────
@app.on_message(filters.command("tagadmins") & filters.group)
async def tagadmins_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text(
            "<blockquote>❌ Sirf admins use kar sakte hain.</blockquote>",
            parse_mode="html"
        )

    custom_msg = " ".join(message.command[1:]) if len(message.command) > 1 else "Admins ko tag!"
    admins = []
    try:
        async for m in app.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if not m.user.is_bot and not m.user.is_deleted:
                admins.append(m.user)
    except Exception as e:
        return await message.reply_text(
            f"<blockquote>❌ Error: {e}</blockquote>",
            parse_mode="html"
        )

    if not admins:
        return await message.reply_text(
            "<blockquote>❌ Koi admin nahi mila.</blockquote>",
            parse_mode="html"
        )

    lines = [
        f"<blockquote>📢 <b>{_mention(message.from_user)}</b> ne call kiya:\n🔔 {custom_msg}</blockquote>",
        ""
    ]
    for u in admins:
        lines.append(_mention(u))
        lines.append("")
    await message.reply_text(
        "\n".join(lines).strip(),
        disable_notification=True,
        disable_web_page_preview=True,
        parse_mode="html"
    )


# ─── Good Morning ────────────────────────────────────────────────────────────
@app.on_message(filters.command("gmtag") & filters.group)
async def gmtag_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        return
    if _active_tags.get(message.chat.id):
        return await message.reply_text(
            "<blockquote>⚠️ Tag chal raha hai. /stoptag karo pehle.</blockquote>",
            parse_mode="html"
        )
    extra = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    header = (
        f"🌅 <b>Good Morning, sab logo!</b> ☀️\n"
        f"{'➤ ' + extra + chr(10) if extra else ''}"
        f"Ek naya din hai, fresh start karo! 💪✨"
    )
    asyncio.create_task(_do_tagall(message.chat.id, message.from_user, header))


# ─── Good Night ──────────────────────────────────────────────────────────────
@app.on_message(filters.command("gntag") & filters.group)
async def gntag_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        return
    if _active_tags.get(message.chat.id):
        return await message.reply_text(
            "<blockquote>⚠️ Tag chal raha hai. /stoptag karo pehle.</blockquote>",
            parse_mode="html"
        )
    extra = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    header = (
        f"🌙 <b>Good Night, sab logo!</b> 😴⭐\n"
        f"{'➤ ' + extra + chr(10) if extra else ''}"
        f"Sweet dreams! 💤🌟"
    )
    asyncio.create_task(_do_tagall(message.chat.id, message.from_user, header))


# ─── Good Afternoon ──────────────────────────────────────────────────────────
@app.on_message(filters.command("gdtag") & filters.group)
async def gdtag_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        return
    if _active_tags.get(message.chat.id):
        return await message.reply_text(
            "<blockquote>⚠️ Tag chal raha hai. /stoptag karo pehle.</blockquote>",
            parse_mode="html"
        )
    extra = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    header = (
        f"☀️ <b>Good Afternoon, sab logo!</b> 🌤️\n"
        f"{'➤ ' + extra + chr(10) if extra else ''}"
        f"Din ka middle — energy high rakho! ⚡💪"
    )
    asyncio.create_task(_do_tagall(message.chat.id, message.from_user, header))


# ─── Good Evening ─────────────────────────────────────────────────────────────
@app.on_message(filters.command("gevtag") & filters.group)
async def gevtag_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        return
    if _active_tags.get(message.chat.id):
        return await message.reply_text(
            "<blockquote>⚠️ Tag chal raha hai. /stoptag karo pehle.</blockquote>",
            parse_mode="html"
        )
    extra = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    header = (
        f"🌆 <b>Good Evening, sab logo!</b> 🌇\n"
        f"{'➤ ' + extra + chr(10) if extra else ''}"
        f"Shaam ho gayi — relax karo! 🌙😊"
    )
    asyncio.create_task(_do_tagall(message.chat.id, message.from_user, header))


# ─── Birthday Tag ─────────────────────────────────────────────────────────────
@app.on_message(filters.command("gbdtag") & filters.group)
async def gbdtag_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text(
            "<blockquote>❌ Sirf admins use kar sakte hain.</blockquote>",
            parse_mode="html"
        )
    if _active_tags.get(message.chat.id):
        return await message.reply_text(
            "<blockquote>⚠️ Tag chal raha hai. /stoptag karo pehle.</blockquote>",
            parse_mode="html"
        )

    birthday_person = ""
    if message.reply_to_message and message.reply_to_message.from_user:
        birthday_person = _mention(message.reply_to_message.from_user)
    elif message.entities:
        for ent in message.entities:
            if ent.type.value == "text_mention" and ent.user:
                birthday_person = _mention(ent.user)
                break
            elif ent.type.value == "mention" and message.text:
                uname = message.text[ent.offset + 1: ent.offset + ent.length]
                try:
                    u = await app.get_users(uname)
                    birthday_person = _mention(u)
                    break
                except Exception:
                    pass

    if not birthday_person:
        return await message.reply_text(
            "<blockquote>❌ Kiske birthday hai? Mention karo ya reply karo!</blockquote>",
            parse_mode="html"
        )

    header = (
        f"🎂 <b>Happy Birthday {birthday_person}!</b> 🎉🎈\n\n"
        f"Sabko tag karke wish kara raha hun:\n"
        f"🥳 Aao sab milke wish karo! ❤️"
    )
    asyncio.create_task(_do_tagall(message.chat.id, message.from_user, header))
