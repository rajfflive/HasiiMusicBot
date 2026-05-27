# ==============================================================================
# tagall.py - Tag All Members Feature  (admins only)
# ==============================================================================
# /tagall [msg]     — Sab members ko tag karo
# /tagadmins [msg]  — Sirf admins ko tag karo
# ==============================================================================

import asyncio
from pyrogram import enums, filters, types
from HasiiMusic import app


async def _is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


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
            "<blockquote>❌ ᴏɴʟʏ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ /ᴛᴀɢᴀʟʟ</blockquote>"
        )

    custom_msg = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    sent = await message.reply_text("<blockquote>⏳ ꜰᴇᴛᴄʜɪɴɢ ᴀʟʟ ᴍᴇᴍʙᴇʀꜱ...</blockquote>")

    members = []
    try:
        async for member in app.get_chat_members(message.chat.id):
            if member.user.is_bot or member.user.is_deleted:
                continue
            members.append(member.user)
    except Exception as e:
        return await sent.edit_text(f"<blockquote>❌ Failed: {e}</blockquote>")

    if not members:
        return await sent.edit_text("<blockquote>❌ ɴᴏ ᴍᴇᴍʙᴇʀꜱ ꜰᴏᴜɴᴅ.</blockquote>")

    await sent.delete()

    header = f"<blockquote>📢 <b>ᴛᴀɢɢɪɴɢ ᴀʟʟ {len(members)} ᴍᴇᴍʙᴇʀꜱ</b>"
    if custom_msg:
        header += f"\n\n💬 {custom_msg}"
    header += "</blockquote>\n"

    chunk_size = 5
    for i in range(0, len(members), chunk_size):
        chunk = members[i:i + chunk_size]
        mentions = " ".join(
            f"<a href='tg://user?id={u.id}'>{u.first_name}</a>" for u in chunk
        )
        text = (header if i == 0 else "") + mentions
        try:
            await app.send_message(message.chat.id, text, disable_notification=(i > 0))
        except Exception:
            pass
        await asyncio.sleep(1.5)


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
            "<blockquote>❌ ᴏɴʟʏ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ /ᴛᴀɢᴀᴅᴍɪɴꜱ</blockquote>"
        )

    custom_msg = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    admins = []
    try:
        async for member in app.get_chat_members(
            message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS
        ):
            if member.user.is_bot or member.user.is_deleted:
                continue
            admins.append(member.user)
    except Exception as e:
        return await message.reply_text(f"<blockquote>❌ Failed: {e}</blockquote>")

    if not admins:
        return await message.reply_text("<blockquote>❌ ɴᴏ ᴀᴅᴍɪɴꜱ ꜰᴏᴜɴᴅ.</blockquote>")

    mentions = " ".join(
        f"<a href='tg://user?id={u.id}'>{u.first_name}</a>" for u in admins
    )
    header = f"<blockquote>🔔 <b>ᴀᴅᴍɪɴꜱ ᴍᴇɴᴛɪᴏɴ</b>"
    if custom_msg:
        header += f"\n\n💬 {custom_msg}"
    header += "</blockquote>\n"
    await message.reply_text(header + mentions)
