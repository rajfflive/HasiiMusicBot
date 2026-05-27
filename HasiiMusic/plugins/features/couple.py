# ==============================================================================
# couple.py - Couples Feature
# ==============================================================================
# Commands:
# - /couple @user   — Propose a couple pairing
# - /uncouple       — Remove your couple
# - /mycouple       — Check who your couple is (ya reply pe check karo)
# ==============================================================================

from pyrogram import filters, types

from HasiiMusic import app, db


async def _get_couple(user_id: int):
    return await db.mongo.HasiiTune.couples.find_one({"user_id": user_id})


async def _set_couple(user1_id: int, user2_id: int):
    await db.mongo.HasiiTune.couples.update_one(
        {"user_id": user1_id},
        {"$set": {"user_id": user1_id, "partner_id": user2_id}},
        upsert=True,
    )
    await db.mongo.HasiiTune.couples.update_one(
        {"user_id": user2_id},
        {"$set": {"user_id": user2_id, "partner_id": user1_id}},
        upsert=True,
    )


async def _del_couple(user_id: int):
    doc = await _get_couple(user_id)
    if doc:
        partner_id = doc.get("partner_id")
        await db.mongo.HasiiTune.couples.delete_one({"user_id": user_id})
        if partner_id:
            await db.mongo.HasiiTune.couples.delete_one({"user_id": partner_id})


@app.on_message(filters.command("couple") & filters.group)
async def couple_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass

    if not message.from_user:
        return

    user = message.from_user
    target = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await app.get_users(message.command[1].lstrip("@"))
        except Exception:
            return await message.reply_text(
                "<blockquote>❌ ᴜꜱᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ.</blockquote>"
            )
    else:
        return await message.reply_text(
            "<blockquote>💑 ᴜꜱᴀɢᴇ: <code>/couple @username</code> ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ</blockquote>"
        )

    if target.id == user.id:
        return await message.reply_text(
            "<blockquote>💔 ʏᴏᴜ ᴄᴀɴɴᴏᴛ ʙᴇᴄᴏᴍᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄᴏᴜᴘʟᴇ! 😅</blockquote>"
        )
    if target.is_bot:
        return await message.reply_text(
            "<blockquote>🤖 ʙᴏᴛꜱ ᴄᴀɴɴᴏᴛ ʙᴇ ᴀ ᴄᴏᴜᴘʟᴇ ᴘᴀʀᴛɴᴇʀ!</blockquote>"
        )

    if await _get_couple(user.id):
        return await message.reply_text(
            "<blockquote>💘 ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴀ ᴄᴏᴜᴘʟᴇ!\n"
            "ᴜꜱᴇ /ᴜɴᴄᴏᴜᴘʟᴇ ꜰɪʀꜱᴛ ᴛᴏ ʙʀᴇᴀᴋ ᴜᴘ.</blockquote>"
        )
    if await _get_couple(target.id):
        return await message.reply_text(
            f"<blockquote>💔 {target.mention} ɪꜱ ᴀʟʀᴇᴀᴅʏ ɪɴ ᴀ ᴄᴏᴜᴘʟᴇ!</blockquote>"
        )

    await _set_couple(user.id, target.id)
    await message.reply_text(
        f"<blockquote>💑 <b>ɴᴇᴡ ᴄᴏᴜᴘʟᴇ!</b>\n\n"
        f"❤️ {user.mention} × {target.mention} ❤️\n\n"
        f"ᴡɪꜱʜɪɴɢ ʏᴏᴜ ʙᴏᴛʜ ᴀ ʙᴇᴀᴜᴛɪꜰᴜʟ ᴊᴏᴜʀɴᴇʏ ᴛᴏɢᴇᴛʜᴇʀ! 🌹</blockquote>"
    )


@app.on_message(filters.command("uncouple") & filters.group)
async def uncouple_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass

    if not message.from_user:
        return

    doc = await _get_couple(message.from_user.id)
    if not doc:
        return await message.reply_text(
            "<blockquote>💔 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀ ᴄᴏᴜᴘʟᴇ ʏᴇᴛ.</blockquote>"
        )

    partner_id = doc.get("partner_id")
    partner_mention = ""
    if partner_id:
        try:
            partner = await app.get_users(partner_id)
            partner_mention = partner.mention
        except Exception:
            partner_mention = "ᴜɴᴋɴᴏᴡɴ"

    await _del_couple(message.from_user.id)
    await message.reply_text(
        f"<blockquote>💔 {message.from_user.mention} ᴀɴᴅ {partner_mention} ʜᴀᴠᴇ ʙʀᴏᴋᴇɴ ᴜᴘ.\n\n"
        f"ꜱᴏᴍᴇᴛɪᴍᴇꜱ ᴇɴᴅɪɴɢꜱ ᴀʀᴇ ɴᴇᴄᴇꜱꜱᴀʀʏ ꜰᴏʀ ɴᴇᴡ ʙᴇɢɪɴɴɪɴɢꜱ 🌧️</blockquote>"
    )


@app.on_message(filters.command("mycouple") & filters.group)
async def mycouple_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass

    if not message.from_user:
        return

    check_user = message.from_user
    if message.reply_to_message and message.reply_to_message.from_user:
        check_user = message.reply_to_message.from_user

    doc = await _get_couple(check_user.id)
    if not doc:
        return await message.reply_text(
            f"<blockquote>💔 {check_user.mention} ɪꜱ ɴᴏᴛ ɪɴ ᴀ ᴄᴏᴜᴘʟᴇ ʏᴇᴛ.\n"
            f"ᴜꜱᴇ /ᴄᴏᴜᴘʟᴇ @ᴜꜱᴇʀɴᴀᴍᴇ ᴛᴏ ꜱᴛᴀʀᴛ ᴏɴᴇ 💕</blockquote>"
        )

    try:
        partner = await app.get_users(doc["partner_id"])
        partner_mention = partner.mention
    except Exception:
        partner_mention = "ᴜɴᴋɴᴏᴡɴ"

    await message.reply_text(
        f"<blockquote>💑 <b>ᴄᴏᴜᴘʟᴇ ɪɴꜰᴏ</b>\n\n"
        f"❤️ {check_user.mention}\n"
        f"🩷 {partner_mention}\n\n"
        f"ᴛᴏɢᴇᴛʜᴇʀ ᴀɴᴅ ʜᴀᴘᴘʏ! 🌸</blockquote>"
    )
