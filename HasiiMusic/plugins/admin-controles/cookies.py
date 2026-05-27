import os

from pyrogram import filters, types

from HasiiMusic import app, config

COOKIES_PATH = "HasiiMusic/cookies/cookies.txt"
OWNER_ID = int(getattr(config, "OWNER_ID", 0))


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


@app.on_message(filters.command("setcookies") & filters.private)
async def set_cookies_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner(message.from_user.id):
        return await message.reply_text(
            "<blockquote>❌ ᴏᴡɴᴇʀ ᴏɴʟʏ ᴄᴏᴍᴍᴀɴᴅ.</blockquote>"
        )

    doc = message.document or (
        message.reply_to_message.document
        if message.reply_to_message
        else None
    )

    if not doc:
        return await message.reply_text(
            "<blockquote>📄 ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ <code>cookies.txt</code> ꜰɪʟᴇ ᴡɪᴛʜ /ꜱᴇᴛᴄᴏᴏᴋɪᴇꜱ\n\n"
            "ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ᴄᴏᴏᴋɪᴇꜱ ꜰɪʟᴇ ᴡɪᴛʜ /ꜱᴇᴛᴄᴏᴏᴋɪᴇꜱ</blockquote>"
        )

    status = await message.reply_text("<blockquote>⏳ ᴜᴘʟᴏᴀᴅɪɴɢ ᴄᴏᴏᴋɪᴇꜱ...</blockquote>")
    try:
        os.makedirs(os.path.dirname(COOKIES_PATH), exist_ok=True)
        await app.download_media(doc, file_name=COOKIES_PATH)
        size = os.path.getsize(COOKIES_PATH)
        await status.edit_text(
            f"<blockquote>✅ ᴄᴏᴏᴋɪᴇꜱ ᴜᴘᴅᴀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!\n\n"
            f"📁 ᴘᴀᴛʜ: <code>{COOKIES_PATH}</code>\n"
            f"📦 ꜱɪᴢᴇ: {size} ʙʏᴛᴇꜱ\n\n"
            f"ᴜꜱᴇ /ᴄʜᴇᴄᴋᴄᴏᴏᴋɪᴇꜱ ᴛᴏ ᴠᴇʀɪꜰʏ.</blockquote>"
        )
    except Exception as e:
        await status.edit_text(
            f"<blockquote>❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴀᴠᴇ ᴄᴏᴏᴋɪᴇꜱ:\n{e}</blockquote>"
        )


@app.on_message(filters.command("checkcookies"))
async def check_cookies_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner(message.from_user.id):
        return await message.reply_text(
            "<blockquote>❌ ᴏᴡɴᴇʀ ᴏɴʟʏ ᴄᴏᴍᴍᴀɴᴅ.</blockquote>"
        )

    if not os.path.exists(COOKIES_PATH):
        return await message.reply_text(
            "<blockquote>⚠️ ɴᴏ ᴄᴏᴏᴋɪᴇꜱ ꜰɪʟᴇ ꜰᴏᴜɴᴅ.\n\n"
            "ᴜꜱᴇ /ꜱᴇᴛᴄᴏᴏᴋɪᴇꜱ ᴛᴏ ᴜᴘʟᴏᴀᴅ ᴏɴᴇ.</blockquote>"
        )

    try:
        size = os.path.getsize(COOKIES_PATH)
        mtime = os.path.getmtime(COOKIES_PATH)

        with open(COOKIES_PATH, "r", errors="ignore") as f:
            content = f.read()

        lines = [l for l in content.splitlines() if l.strip() and not l.startswith("#")]
        domains = set()
        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 6:
                domains.add(parts[0].lstrip("."))

        import datetime
        modified = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

        yt_ok = any("youtube" in d or "google" in d for d in domains)
        status_icon = "✅" if yt_ok else "⚠️"
        yt_status = "ᴘʀᴇꜱᴇɴᴛ" if yt_ok else "ɴᴏᴛ ꜰᴏᴜɴᴅ"

        domain_list = "\n".join(f"  • {d}" for d in sorted(domains)[:10])
        if len(domains) > 10:
            domain_list += f"\n  ... +{len(domains) - 10} ᴍᴏʀᴇ"

        await message.reply_text(
            f"<blockquote><b>🍪 ᴄᴏᴏᴋɪᴇꜱ ꜱᴛᴀᴛᴜꜱ</b>\n\n"
            f"{status_icon} ʏᴏᴜᴛᴜʙᴇ ᴄᴏᴏᴋɪᴇꜱ: {yt_status}\n"
            f"📁 ꜰɪʟᴇ ꜱɪᴢᴇ: {size:,} ʙʏᴛᴇꜱ\n"
            f"🕐 ʟᴀꜱᴛ ᴜᴘᴅᴀᴛᴇᴅ: {modified}\n"
            f"📊 ᴛᴏᴛᴀʟ ᴇɴᴛʀɪᴇꜱ: {len(lines)}\n"
            f"🌐 ᴅᴏᴍᴀɪɴꜱ:\n{domain_list}</blockquote>"
        )
    except Exception as e:
        await message.reply_text(
            f"<blockquote>❌ ᴇʀʀᴏʀ ʀᴇᴀᴅɪɴɢ ᴄᴏᴏᴋɪᴇꜱ:\n{e}</blockquote>"
        )


@app.on_message(filters.command("delcookies") & filters.private)
async def del_cookies_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner(message.from_user.id):
        return
    if not os.path.exists(COOKIES_PATH):
        return await message.reply_text(
            "<blockquote>ℹ️ ɴᴏ ᴄᴏᴏᴋɪᴇꜱ ꜰɪʟᴇ ᴛᴏ ᴅᴇʟᴇᴛᴇ.</blockquote>"
        )
    try:
        os.remove(COOKIES_PATH)
        await message.reply_text(
            "<blockquote>🗑 ᴄᴏᴏᴋɪᴇꜱ ᴅᴇʟᴇᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.</blockquote>"
        )
    except Exception as e:
        await message.reply_text(f"<blockquote>❌ {e}</blockquote>")
