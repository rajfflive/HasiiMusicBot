# new_chat.py - MODIFIED (branding uses BOT_NAME env var)

from pyrogram import filters, types
from HasiiMusic import app, config


@app.on_message(filters.new_chat_members & filters.group)
async def new_chat_member(_, message: types.Message):
    for member in message.new_chat_members:
        if member.id == app.id:
            chat = message.chat
            chat_name = chat.title
            chat_id = chat.id
            chat_username = f"@{chat.username}" if chat.username else "ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ"
            members_count = await app.get_chat_members_count(chat_id)
            added_by = message.from_user
            added_by_name = added_by.mention if added_by else "ᴜɴᴋɴᴏᴡɴ"
            # Branding: BOT_NAME env var se aata hai, fallback app.name
            bot_display = getattr(config, "BOT_NAME", None) or app.name or "@aavyaxbots music bot"

            text = f"""<blockquote>🟢 <b>˹{bot_display}˼ ᴀᴅᴅᴇᴅ ɪɴ ᴀ ɴᴇᴡ ɢʀᴏᴜᴘ</b></blockquote>

<blockquote>
🔖 <b>ᴄʜᴀᴛ ɴᴀᴍᴇ:</b> {chat_name}
🆔 <b>ᴄʜᴀᴛ ɪᴅ:</b> <code>{chat_id}</code>
👤 <b>ᴄʜᴀᴛ ᴜꜱᴇʀɴᴀᴍᴇ:</b> {chat_username}
🔗 <b>ᴄʜᴀᴛ ʟɪɴᴋ:</b> {f"https://t.me/{chat.username}" if chat.username else "ᴘʀɪᴠᴀᴛᴇ"}
👥 <b>ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs:</b> {members_count}
🤵 <b>ᴀᴅᴅᴇᴅ ʙʏ:</b> {added_by_name}
</blockquote>
"""
            try:
                await app.send_photo(
                    chat_id=config.LOGGER_ID,
                    photo=config.START_IMG,
                    caption=text,
                )
            except Exception as e:
                print(f"Failed to send new chat notification: {e}")
            break


@app.on_message(filters.left_chat_member & filters.group)
async def left_chat_member(_, message: types.Message):
    if message.left_chat_member.id == app.id:
        chat = message.chat
        chat_name = chat.title
        chat_id = chat.id
        chat_username = f"@{chat.username}" if chat.username else "ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ"
        removed_by = message.from_user
        removed_by_name = removed_by.mention if removed_by else "ᴜɴᴋɴᴏᴡɴ"
        bot_display = getattr(config, "BOT_NAME", None) or app.name or "ᴍᴜꜱɪᴄ ʙᴏᴛ"

        text = f"""<blockquote>🔴 <b>˹{bot_display}˼ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴀ ɢʀᴏᴜᴘ</b></blockquote>

<blockquote>
🔖 <b>ᴄʜᴀᴛ ɴᴀᴍᴇ:</b> {chat_name}
🆔 <b>ᴄʜᴀᴛ ɪᴅ:</b> <code>{chat_id}</code>
👤 <b>ᴄʜᴀᴛ ᴜꜱᴇʀɴᴀᴍᴇ:</b> {chat_username}
🔗 <b>ᴄʜᴀᴛ ʟɪɴᴋ:</b> {f"https://t.me/{chat.username}" if chat.username else "ᴘʀɪᴠᴀᴛᴇ"}
🚫 <b>ʀᴇᴍᴏᴠᴇᴅ ʙʏ:</b> {removed_by_name}
</blockquote>
"""
        try:
            await app.send_photo(
                chat_id=config.LOGGER_ID,
                photo=config.START_IMG,
                caption=text,
            )
        except Exception as e:
            print(f"Failed to send left chat notification: {e}")
