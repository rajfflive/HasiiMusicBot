# ==============================================================================
# couple.py - Couples Feature
# ==============================================================================
# Commands:
# - /couple @user   — Propose a couple pairing
# - /uncouple       — Remove your couple
# - /mycouple       — Check who your couple is (ya reply pe check karo)
# ==============================================================================

import random

from pyrogram import enums, filters, types

from HasiiMusic import app, db


COUPLE_GIFS = [
    "https://media.giphy.com/media/l4pTdcifPZLpDjL1e/giphy.gif",
    "https://media.giphy.com/media/xT1XGYy9NPhWRPp4re/giphy.gif",
    "https://media.giphy.com/media/TJ9LupxFBNUgo/giphy.gif",
    "https://media.giphy.com/media/3o6Zt6KHxJTbXCnSvu/giphy.gif",
    "https://media.giphy.com/media/26BRrSvJEqmYfdBC4/giphy.gif",
]


async def _get_couple(user_id: int):
    return await db.mongo.HasiiTune.couples.find_one({"user_id": user_id})


async def _set_couple(user1_id: int, user2_id: int):
    for uid, pid in [(user1_id, user2_id), (user2_id, user1_id)]:
        await db.mongo.HasiiTune.couples.update_one(
            {"user_id": uid},
            {"$set": {"user_id": uid, "partner_id": pid}},
            upsert=True,
        )


async def _del_couple(user_id: int):
    doc = await _get_couple(user_id)
    if doc:
        partner_id = doc.get("partner_id")
        await db.mongo.HasiiTune.couples.delete_one({"user_id": user_id})
        if partner_id:
            await db.mongo.HasiiTune.couples.delete_one({"user_id": partner_id})


async def _send_couple_gif(chat_id: int, u1: types.User, u2: types.User):
    m1 = f"<a href='tg://user?id={u1.id}'>{u1.first_name}</a>"
    m2 = f"<a href='tg://user?id={u2.id}'>{u2.first_name}</a>"
    caption = (
        f"╔══════════════════╗\n"
        f"   💑  ɴᴇᴡ ᴄᴏᴜᴘʟᴇ ᴀʟᴇʀᴛ  💑\n"
        f"╚══════════════════╝\n\n"
        f"  ❤️  {m1}\n"
        f"  🩷  {m2}\n\n"
        f"  ᴡɪꜱʜɪɴɢ ʏᴏᴜ ʙᴏᴛʜ ᴀ ʙᴇᴀᴜᴛɪꜰᴜʟ\n"
        f"  ᴊᴏᴜʀɴᴇʏ ᴛᴏɢᴇᴛʜᴇʀ ᴀʟᴡᴀʏꜱ 🌹"
    )
    gif_url = random.choice(COUPLE_GIFS)
    try:
        await app.send_animation(chat_id, animation=gif_url, caption=caption)
    except Exception:
        try:
            await app.send_message(chat_id, f"<blockquote>{caption}</blockquote>")
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
        await _send_couple_gif(chat_id, u1, u2)
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
            "<blockquote>💔 ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴄᴏᴜᴘʟᴇ ᴡɪᴛʜ ʏᴏᴜʀꜱᴇʟꜰ! 😅</blockquote>"
        )
    if target.is_bot:
        return await message.reply_text(
            "<blockquote>🤖 ʙᴏᴛꜱ ᴄᴀɴɴᴏᴛ ʙᴇ ᴀ ᴄᴏᴜᴘʟᴇ ᴘᴀʀᴛɴᴇʀ!</blockquote>"
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
    await _send_couple_gif(chat_id, user, target)


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
    partner_mention = "ᴜɴᴋɴᴏᴡɴ"
    if partner_id:
        try:
            partner = await app.get_users(partner_id)
            partner_mention = partner.mention
        except Exception:
            pass

    await _del_couple(message.from_user.id)
    await message.reply_text(
        f"<blockquote>💔 {message.from_user.mention} ᴀɴᴅ {partner_mention} ʜᴀᴠᴇ\n"
        f"ʙʀᴏᴋᴇɴ ᴜᴘ 🌧️\n\n"
        f"ꜱᴏᴍᴇᴛɪᴍᴇꜱ ᴇɴᴅɪɴɢꜱ ʟᴇᴀᴅ ᴛᴏ ɴᴇᴡ ʙᴇɢɪɴɴɪɴɢꜱ.</blockquote>"
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
            f"ᴜꜱᴇ /ᴄᴏᴜᴘʟᴇ ᴛᴏ ꜰɪɴᴅ ᴀ ᴍᴀᴛᴄʜ 💕</blockquote>"
        )

    try:
        partner = await app.get_users(doc["partner_id"])
        partner_mention = partner.mention
    except Exception:
        partner_mention = "ᴜɴᴋɴᴏᴡɴ"

    await message.reply_text(
        f"╔══════════════════╗\n"
        f"   💑  ᴄᴏᴜᴘʟᴇ ɪɴꜰᴏ  💑\n"
        f"╚══════════════════╝\n\n"
        f"  ❤️  {check_user.mention}\n"
        f"  🩷  {partner_mention}\n\n"
        f"  ᴛᴏɢᴇᴛʜᴇʀ ᴀɴᴅ ʜᴀᴘᴘʏ! 🌸"
    )
