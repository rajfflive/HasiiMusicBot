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


@app.on_message(filters.command("stoptag") & filters.group)
async def stoptag_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user:
        return
    if not await _is_admin(message.chat.id, message.from_user.id):
        return
    chat_id = message.chat.id
    if _active_tags.get(chat_id):
        _active_tags[chat_id] = False
        await message.reply_text("<blockquote>🛑 ᴛᴀɢ ꜱᴛᴏᴘᴘᴇᴅ.</blockquote>")
    else:
        await message.reply_text("<blockquote>ℹ️ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴛᴀɢ ꜱᴇꜱꜱɪᴏɴ.</blockquote>")


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
            "<blockquote>❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ /ᴛᴀɢᴀʟʟ</blockquote>"
        )

    chat_id = message.chat.id
    if _active_tags.get(chat_id):
        return await message.reply_text(
            "<blockquote>⚠️ ᴀʟʀᴇᴀᴅʏ ᴛᴀɢɢɪɴɢ. ᴜꜱᴇ /ꜱᴛᴏᴘᴛᴀɢ ᴛᴏ ꜱᴛᴏᴘ.</blockquote>"
        )

    custom_msg = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    status = await message.reply_text("<blockquote>⏳ ꜰᴇᴛᴄʜɪɴɢ ᴍᴇᴍʙᴇʀꜱ...</blockquote>")

    members = []
    try:
        async for m in app.get_chat_members(chat_id):
            if m.user.is_bot or m.user.is_deleted:
                continue
            members.append(m.user)
    except Exception as e:
        return await status.edit_text(f"<blockquote>❌ Error: {e}</blockquote>")

    if not members:
        return await status.edit_text("<blockquote>❌ ɴᴏ ᴍᴇᴍʙᴇʀꜱ ꜰᴏᴜɴᴅ.</blockquote>")

    await status.delete()
    _active_tags[chat_id] = True

    chunk_size = 5
    for i in range(0, len(members), chunk_size):
        if not _active_tags.get(chat_id):
            break

        chunk = members[i : i + chunk_size]

        # Har message mein: custom message (agar hai) + ek line pe ek mention
        lines = []
        if custom_msg:
            lines.append(f"<blockquote>📢 {custom_msg}</blockquote>")
        for u in chunk:
            lines.append(f"<a href='tg://user?id={u.id}'>{u.first_name}</a>")

        text = "\n".join(lines)
        try:
            await app.send_message(
                chat_id,
                text,
                disable_notification=True,
                disable_web_page_preview=True,
            )
        except Exception:
            pass
        await asyncio.sleep(1.5)

    _active_tags.pop(chat_id, None)


@app.on_message(filters.command("tagadmins") & filters.group)
async def tagadmins_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user:
        return
    if not await _is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text(
            "<blockquote>❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ /ᴛᴀɢᴀᴅᴍɪɴꜱ</blockquote>"
        )

    chat_id = message.chat.id
    custom_msg = " ".join(message.command[1:]) if len(message.command) > 1 else ""

    admins = []
    try:
        async for m in app.get_chat_members(
            chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS
        ):
            if m.user.is_bot or m.user.is_deleted:
                continue
            admins.append(m.user)
    except Exception as e:
        return await message.reply_text(f"<blockquote>❌ Error: {e}</blockquote>")

    if not admins:
        return await message.reply_text("<blockquote>❌ ɴᴏ ᴀᴅᴍɪɴꜱ ꜰᴏᴜɴᴅ.</blockquote>")

    lines = []
    if custom_msg:
        lines.append(f"<blockquote>🔔 {custom_msg}</blockquote>")
    for u in admins:
        lines.append(f"<a href='tg://user?id={u.id}'>{u.first_name}</a>")

    await message.reply_text(
        "\n".join(lines),
        disable_notification=True,
        disable_web_page_preview=True,
    )
