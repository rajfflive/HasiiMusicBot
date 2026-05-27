import random

from pyrogram import filters, types

from HasiiMusic import app, db


COUPLE_GIFS = [
    "https://media2.giphy.com/media/8Vk5ZW0vu4Kha/giphy.gif",
    "https://media2.giphy.com/media/l4pTdcifPZLpDjL1e/giphy.gif",
    "https://media2.giphy.com/media/OR4N5Y6ePt684/giphy.gif",
    "https://media2.giphy.com/media/zTZrYp2C7JMly/giphy.gif",
    "https://media2.giphy.com/media/CwyORe13mVKiQ/giphy.gif",
]

LOVE_QUOTES = [
    "ɪɴ ʏᴏᴜʀ ᴀʀᴍꜱ ɪꜱ ᴇxᴀᴄᴛʟʏ ᴡʜᴇʀᴇ ɪ ʙᴇʟᴏɴɢ 🌹",
    "ʏᴏᴜ ᴀʀᴇ ᴛʜᴇ ʙᴇꜱᴛ ᴛʜɪɴɢ ᴛʜᴀᴛ ᴇᴠᴇʀ ʜᴀᴘᴘᴇɴᴇᴅ ᴛᴏ ᴍᴇ 💫",
    "ʟᴏᴠᴇ ɪꜱ ɴᴏᴛ ᴊᴜꜱᴛ ᴀ ꜰᴇᴇʟɪɴɢ, ɪᴛ'ꜱ ᴀ ᴘʀᴏᴍɪꜱᴇ 🌸",
    "ᴡɪᴛʜ ʏᴏᴜ, ᴇᴠᴇʀʏ ᴍᴏᴍᴇɴᴛ ꜰᴇᴇʟꜱ ʟɪᴋᴇ ᴀ ᴅʀᴇᴀᴍ ✨",
    "ɪ ᴄʜᴏᴏꜱᴇ ʏᴏᴜ. ᴀɴᴅ ɪ'ʟʟ ᴄʜᴏᴏꜱᴇ ʏᴏᴜ ᴏᴠᴇʀ ᴀɴᴅ ᴏᴠᴇʀ 💕",
    "ʏᴏᴜ ᴀʀᴇ ᴍʏ ꜱᴜɴꜱʜɪɴᴇ ᴏɴ ᴀ ʀᴀɪɴʏ ᴅᴀʏ ☀️",
    "ᴇᴠᴇʀʏ ʟᴏᴠᴇ ꜱᴛᴏʀʏ ɪꜱ ʙᴇᴀᴜᴛɪꜰᴜʟ, ʙᴜᴛ ᴏᴜʀꜱ ɪꜱ ᴍʏ ꜰᴀᴠᴏᴜʀɪᴛᴇ 💖",
    "ᴛᴏɢᴇᴛʜᴇʀ ɪꜱ ᴀ ᴡᴏɴᴅᴇʀꜰᴜʟ ᴘʟᴀᴄᴇ ᴛᴏ ʙᴇ 🫶",
    "ʏᴏᴜ ᴀʀᴇ ᴍʏ ꜰᴀᴠᴏᴜʀɪᴛᴇ ʜᴇʟʟᴏ ᴀɴᴅ ʜᴀʀᴅᴇꜱᴛ ɢᴏᴏᴅʙʏᴇ 🥺",
    "ɪ ꜰᴀʟʟ ɪɴ ʟᴏᴠᴇ ᴡɪᴛʜ ʏᴏᴜ ᴀ ʟɪᴛᴛʟᴇ ᴍᴏʀᴇ ᴇᴠᴇʀʏ ᴅᴀʏ 🌺",
]


async def _get_couple(user_id: int):
    return await db.mongo.HasiiTune.couples.find_one({"user_id": user_id})


async def _set_couple(u1: int, u2: int):
    for uid, pid in [(u1, u2), (u2, u1)]:
        await db.mongo.HasiiTune.couples.update_one(
            {"user_id": uid},
            {"$set": {"user_id": uid, "partner_id": pid}},
            upsert=True,
        )


async def _del_couple(user_id: int):
    doc = await _get_couple(user_id)
    if doc:
        pid = doc.get("partner_id")
        await db.mongo.HasiiTune.couples.delete_one({"user_id": user_id})
        if pid:
            await db.mongo.HasiiTune.couples.delete_one({"user_id": pid})


async def _send_couple_card(chat_id: int, u1: types.User, u2: types.User):
    m1 = f"<a href='tg://user?id={u1.id}'>{u1.first_name}</a>"
    m2 = f"<a href='tg://user?id={u2.id}'>{u2.first_name}</a>"
    quote = random.choice(LOVE_QUOTES)

    caption = (
        f"<b>╔══[ 💑 ɴᴇᴡ ᴄᴏᴜᴘʟᴇ ]══╗</b>\n\n"
        f"  ❤️  {m1}\n"
        f"         ×\n"
        f"  🩷  {m2}\n\n"
        f"<blockquote>{quote}</blockquote>\n\n"
        f"<b>╚════════════════╝</b>"
    )

    for gif in random.sample(COUPLE_GIFS, len(COUPLE_GIFS)):
        try:
            await app.send_animation(chat_id, animation=gif, caption=caption)
            return
        except Exception:
            continue
    try:
        await app.send_message(chat_id, caption, disable_web_page_preview=True)
    except Exception:
        pass


@app.on_message(filters.command("couple") & filters.group)
async def couple_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user:
        return

    chat_id = message.chat.id
    user = message.from_user

    if len(message.command) == 1 and not message.reply_to_message:
        members = []
        try:
            async for m in app.get_chat_members(chat_id):
                if m.user.is_bot or m.user.is_deleted:
                    continue
                members.append(m.user)
        except Exception as e:
            return await message.reply_text(f"<blockquote>❌ Error: {e}</blockquote>")

        if len(members) < 2:
            return await message.reply_text(
                "<blockquote>❌ ɴᴏᴛ ᴇɴᴏᴜɢʜ ᴍᴇᴍʙᴇʀꜱ!</blockquote>"
            )
        u1, u2 = random.sample(members, 2)
        await _set_couple(u1.id, u2.id)
        await _send_couple_card(chat_id, u1, u2)
        return

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
    if not target:
        return
    if target.id == user.id:
        return await message.reply_text(
            "<blockquote>💔 ʏᴏᴜ ᴄᴀɴ'ᴛ ᴄᴏᴜᴘʟᴇ ᴡɪᴛʜ ʏᴏᴜʀꜱᴇʟꜰ 😅</blockquote>"
        )
    if target.is_bot:
        return await message.reply_text(
            "<blockquote>🤖 ʙᴏᴛꜱ ᴄᴀɴɴᴏᴛ ʙᴇ ᴄᴏᴜᴘʟᴇᴅ!</blockquote>"
        )
    if await _get_couple(user.id):
        return await message.reply_text(
            "<blockquote>💘 ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴀ ᴄᴏᴜᴘʟᴇ!\n"
            "ᴜꜱᴇ /ᴜɴᴄᴏᴜᴘʟᴇ ꜰɪʀꜱᴛ.</blockquote>"
        )
    if await _get_couple(target.id):
        return await message.reply_text(
            f"<blockquote>💔 {target.mention} ɪꜱ ᴀʟʀᴇᴀᴅʏ ɪɴ ᴀ ᴄᴏᴜᴘʟᴇ!</blockquote>"
        )
    await _set_couple(user.id, target.id)
    await _send_couple_card(chat_id, user, target)


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
    pm = "ᴜɴᴋɴᴏᴡɴ"
    if pid := doc.get("partner_id"):
        try:
            p = await app.get_users(pid)
            pm = p.mention
        except Exception:
            pass
    await _del_couple(message.from_user.id)
    await message.reply_text(
        f"<blockquote>💔 {message.from_user.mention} ᴀɴᴅ {pm} ʜᴀᴠᴇ ʙʀᴏᴋᴇɴ ᴜᴘ 🌧️\n\n"
        f"ꜱᴏᴍᴇᴛɪᴍᴇꜱ ᴇɴᴅɪɴɢꜱ ʟᴇᴀᴅ ᴛᴏ ʙᴇᴛᴛᴇʀ ʙᴇɢɪɴɴɪɴɢꜱ 🌱</blockquote>"
    )


@app.on_message(filters.command("mycouple") & filters.group)
async def mycouple_cmd(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.from_user:
        return
    check = message.from_user
    if message.reply_to_message and message.reply_to_message.from_user:
        check = message.reply_to_message.from_user
    doc = await _get_couple(check.id)
    if not doc:
        return await message.reply_text(
            f"<blockquote>💔 {check.mention} ɪꜱ ɴᴏᴛ ɪɴ ᴀ ᴄᴏᴜᴘʟᴇ ʏᴇᴛ.\n"
            f"ᴜꜱᴇ /ᴄᴏᴜᴘʟᴇ ᴛᴏ ꜰɪɴᴅ ᴀ ᴍᴀᴛᴄʜ 💕</blockquote>"
        )
    try:
        partner = await app.get_users(doc["partner_id"])
        pm = partner.mention
    except Exception:
        pm = "ᴜɴᴋɴᴏᴡɴ"
    await message.reply_text(
        f"<b>╔══[ 💑 ᴄᴏᴜᴘʟᴇ ɪɴꜰᴏ ]══╗</b>\n\n"
        f"  ❤️  {check.mention}\n"
        f"         ×\n"
        f"  🩷  {pm}\n\n"
        f"<blockquote>ᴛᴏɢᴇᴛʜᴇʀ ᴀɴᴅ ʜᴀᴘᴘʏ ᴀʟᴡᴀʏꜱ 🌸</blockquote>\n\n"
        f"<b>╚════════════════╝</b>"
    )
