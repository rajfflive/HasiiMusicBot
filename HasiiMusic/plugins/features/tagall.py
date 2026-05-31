"""
TagAll Plugin — v3 with GIF Manager
Commands:
  /tagall [msg]    - Tag all members
  /tagadmins [msg] - Tag only admins
  /stoptag         - Stop active tagging
  /gmtag [msg]     - Good Morning tag with GIF
  /gntag [msg]     - Good Night tag with GIF
  /gdtag [msg]     - Good Afternoon tag with GIF
  /gevtag [msg]    - Good Evening tag with GIF
  /gbdtag @user    - Birthday tag for someone with GIF

GIF Management (owner/sudo/admin only):
  /setgmgif        - Reply to GIF → set for Good Morning
  /setgngif        - Reply to GIF → set for Good Night
  /setgdgif        - Reply to GIF → set for Good Afternoon
  /setgevgif       - Reply to GIF → set for Good Evening
  /setgbdgif       - Reply to GIF → set for Birthday
  /listgmgif / /listgngif / etc. — list GIFs for each type
  /rmgmgif <n>     - Remove a GIF by number (same for others)
"""

import asyncio
from pyrogram import enums, filters, types
from HasiiMusic import app
from HasiiMusic.helpers.gif_manager import get_random_gif, register_gif_commands

_active_tags: dict[int, bool] = {}

# ─── Register GIF commands for each greeting type ────────────────────────────
register_gif_commands(app, "gmtag", "gm")
register_gif_commands(app, "gntag", "gn")
register_gif_commands(app, "gdtag", "gd")
register_gif_commands(app, "gevtag", "gev")
register_gif_commands(app, "gbdtag", "gbd")


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


async def _do_tagall(
    chat_id: int,
    trigger_user,
    header_text: str,
    gif_type: str = None,
    chunk_size: int = 4,
    delay: float = 1.5
):
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
            parse_mode=enums.ParseMode.HTML
        )
        return

    if not members:
        await app.send_message(
            chat_id,
            "<blockquote>❌ Koi member nahi mila.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
        return

    _active_tags[chat_id] = True

    trigger_line = f"📢 <b>{_mention(trigger_user)}</b> ne tag kiya:" if trigger_user else "📢 Tag:"
    header_msg = f"<blockquote>{trigger_line}\n{header_text}</blockquote>"

    # Send GIF with header if gif_type is given
    if gif_type:
        gif = get_random_gif(gif_type)
        if gif:
            try:
                await app.send_animation(
                    chat_id, gif,
                    caption=header_msg,
                    parse_mode=enums.ParseMode.HTML,
                    disable_notification=True,
                )
            except Exception:
                await app.send_message(
                    chat_id, header_msg,
                    disable_notification=True,
                    disable_web_page_preview=True,
                    parse_mode=enums.ParseMode.HTML
                )
        else:
            await app.send_message(
                chat_id, header_msg,
                disable_notification=True,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
    else:
        await app.send_message(
            chat_id, header_msg,
            disable_notification=True,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML
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
                parse_mode=enums.ParseMode.HTML
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
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text(
            "<blockquote>ℹ️ Koi active tag nahi hai.</blockquote>",
            parse_mode=enums.ParseMode.HTML
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
            parse_mode=enums.ParseMode.HTML
        )
    if _active_tags.get(message.chat.id):
        return await message.reply_text(
            "<blockquote>⚠️ Pehle se tag chal raha hai. /stoptag karo.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

    custom_msg = " ".join(message.command[1:]) if len(message.command) > 1 else "Sabko tag kar raha hun!"
    asyncio.create_task(
        _do_tagall(message.chat.id, message.from_user, f"📣 {custom_msg}")
    )


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
            parse_mode=enums.ParseMode.HTML
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
            parse_mode=enums.ParseMode.HTML
        )

    if not admins:
        return await message.reply_text(
            "<blockquote>❌ Koi admin nahi mila.</blockquote>",
            parse_mode=enums.ParseMode.HTML
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
        parse_mode=enums.ParseMode.HTML
    )


# ─── Good Morning ─────────────────────────────────────────────────────────────
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
            parse_mode=enums.ParseMode.HTML
        )
    extra = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    header = (
        f"🌅 <b>Good Morning!</b> ☀️\n"
        f"Uthho sab! Naya din aaya hai!\n"
        f"{extra}"
    )
    asyncio.create_task(
        _do_tagall(message.chat.id, message.from_user, header, gif_type="gmtag")
    )


# ─── Good Night ───────────────────────────────────────────────────────────────
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
            parse_mode=enums.ParseMode.HTML
        )
    extra = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    header = (
        f"🌙 <b>Good Night!</b> 💤\n"
        f"Neend acchi aaye sabko!\n"
        f"{extra}"
    )
    asyncio.create_task(
        _do_tagall(message.chat.id, message.from_user, header, gif_type="gntag")
    )


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
            parse_mode=enums.ParseMode.HTML
        )
    extra = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    header = (
        f"☀️ <b>Good Afternoon!</b> 🌤️\n"
        f"Dopahar mubarak ho sabko!\n"
        f"{extra}"
    )
    asyncio.create_task(
        _do_tagall(message.chat.id, message.from_user, header, gif_type="gdtag")
    )


# ─── Good Evening ────────────────────────────────────────────────────────────
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
            parse_mode=enums.ParseMode.HTML
        )
    extra = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    header = (
        f"🌆 <b>Good Evening!</b> 🌇\n"
        f"Shaam mubarak sabko!\n"
        f"{extra}"
    )
    asyncio.create_task(
        _do_tagall(message.chat.id, message.from_user, header, gif_type="gevtag")
    )


# ─── Birthday ─────────────────────────────────────────────────────────────────
@app.on_message(filters.command("gbdtag") & filters.group)
async def gbdtag_cmd(client, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        return

    # Find birthday person
    bday_user = None
    if message.reply_to_message and message.reply_to_message.from_user:
        bday_user = message.reply_to_message.from_user
    elif message.entities:
        for ent in message.entities:
            if ent.type.value == "text_mention" and ent.user:
                bday_user = ent.user
                break
            elif ent.type.value == "mention" and message.text:
                uname = message.text[ent.offset + 1: ent.offset + ent.length]
                try:
                    bday_user = await client.get_users(uname)
                    break
                except Exception:
                    pass

    bday_name = bday_user.first_name if bday_user else "Kisi ka"
    bday_mention = bday_user.mention if bday_user else "🎂"

    if _active_tags.get(message.chat.id):
        return await message.reply_text(
            "<blockquote>⚠️ Tag chal raha hai. /stoptag karo pehle.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

    header = (
        f"🎂 <b>Birthday Mubarak {bday_mention}!</b> 🎉\n"
        f"Sabse wish karo aaj ke birthday star ko! 🎁\n"
        f"🥳 Happy Birthday {bday_name}! Bahut saari khushiyaan milein!"
    )
    asyncio.create_task(
        _do_tagall(message.chat.id, message.from_user, header, gif_type="gbdtag")
    )
