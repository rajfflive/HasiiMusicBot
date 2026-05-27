# ==============================================================================
# welcome.py - Custom Welcome Messages per Group
# ==============================================================================
# /setwelcome [text]     — Group welcome set karo (admins + owner)
# /delwelcome            — Welcome hatao
# /welcome               — Preview dekho
# /setglobalwelcome [t]  — Default welcome sab groups ke liye (owner only, private)
# /delglobalwelcome      — Global welcome hatao (owner only, private)
#
# Variables: {mention} {first} {username} {count} {title}
# ==============================================================================

from pyrogram import enums, filters, types
from HasiiMusic import app, config, db


async def _get_welcome(chat_id: int) -> str | None:
    doc = await db.mongo.HasiiTune.welcome.find_one({"chat_id": chat_id})
    return doc.get("text") if doc else None


async def _set_welcome(chat_id: int, text: str):
    await db.mongo.HasiiTune.welcome.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id, "text": text}},
        upsert=True,
    )


async def _del_welcome(chat_id: int):
    await db.mongo.HasiiTune.welcome.delete_one({"chat_id": chat_id})


async def _is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


def _format_welcome(text: str, user: types.User, chat: types.Chat, count: int) -> str:
    first = user.first_name or ""
    username = f"@{user.username}" if user.username else first
    mention = f"<a href='tg://user?id={user.id}'>{first}</a>"
    return (
        text
        .replace("{mention}", mention)
        .replace("{first}", first)
        .replace("{username}", username)
        .replace("{count}", str(count))
        .replace("{title}", chat.title or "")
    )


@app.on_message(filters.new_chat_members & filters.group, group=5)
async def welcome_new_member(_, message: types.Message):
    chat = message.chat
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        welcome_text = await _get_welcome(chat.id)
        if not welcome_text:
            welcome_text = await _get_welcome(0)  # global default
        if not welcome_text:
            continue
        try:
            count = await app.get_chat_members_count(chat.id)
        except Exception:
            count = 0
        formatted = _format_welcome(welcome_text, member, chat, count)
        try:
            await message.reply_text(formatted, disable_web_page_preview=True)
        except Exception:
            pass


@app.on_message(filters.command("setwelcome") & filters.group)
async def setwelcome_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user:
        return
    is_owner = message.from_user.id == config.OWNER_ID
    if not is_owner and not await _is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text(
            "<blockquote>❌ ᴏɴʟʏ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ꜱᴇᴛ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</blockquote>"
        )
    if len(message.command) < 2:
        return await message.reply_text(
            "<blockquote>📝 <b>ᴜꜱᴀɢᴇ:</b> <code>/setwelcome Your message</code>\n\n"
            "<b>Variables:</b> {mention} {first} {username} {count} {title}</blockquote>"
        )
    text = " ".join(message.command[1:])
    await _set_welcome(message.chat.id, text)
    await message.reply_text(
        f"<blockquote>✅ ᴡᴇʟᴄᴏᴍᴇ ꜱᴇᴛ ꜰᴏʀ <b>{message.chat.title}</b>!</blockquote>"
    )


@app.on_message(filters.command("delwelcome") & filters.group)
async def delwelcome_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user:
        return
    is_owner = message.from_user.id == config.OWNER_ID
    if not is_owner and not await _is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text(
            "<blockquote>❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴅᴏ ᴛʜɪꜱ.</blockquote>"
        )
    await _del_welcome(message.chat.id)
    await message.reply_text("<blockquote>🗑️ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇꜱꜱᴀɢᴇ ʀᴇᴍᴏᴠᴇᴅ.</blockquote>")


@app.on_message(filters.command("welcome") & filters.group)
async def welcome_preview_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    text = await _get_welcome(message.chat.id) or await _get_welcome(0)
    if not text:
        return await message.reply_text(
            "<blockquote>ℹ️ ɴᴏ ᴡᴇʟᴄᴏᴍᴇ ꜱᴇᴛ. ᴜꜱᴇ /ꜱᴇᴛᴡᴇʟᴄᴏᴍᴇ</blockquote>"
        )
    if not message.from_user:
        return
    try:
        count = await app.get_chat_members_count(message.chat.id)
    except Exception:
        count = 0
    preview = _format_welcome(text, message.from_user, message.chat, count)
    await message.reply_text(
        f"<blockquote>👁️ <b>ᴘʀᴇᴠɪᴇᴡ:</b></blockquote>\n\n{preview}",
        disable_web_page_preview=True,
    )


@app.on_message(filters.command("setglobalwelcome") & filters.private)
async def setglobalwelcome_cmd(_, message: types.Message):
    if not message.from_user or message.from_user.id != config.OWNER_ID:
        return
    if len(message.command) < 2:
        return await message.reply_text(
            "<blockquote>📝 /setglobalwelcome [text]\nVariables: {mention} {first} {username} {count} {title}</blockquote>"
        )
    await _set_welcome(0, " ".join(message.command[1:]))
    await message.reply_text("<blockquote>✅ ɢʟᴏʙᴀʟ ᴡᴇʟᴄᴏᴍᴇ ꜱᴇᴛ!</blockquote>")


@app.on_message(filters.command("delglobalwelcome") & filters.private)
async def delglobalwelcome_cmd(_, message: types.Message):
    if not message.from_user or message.from_user.id != config.OWNER_ID:
        return
    await _del_welcome(0)
    await message.reply_text("<blockquote>🗑️ ɢʟᴏʙᴀʟ ᴡᴇʟᴄᴏᴍᴇ ʀᴇᴍᴏᴠᴇᴅ.</blockquote>")
