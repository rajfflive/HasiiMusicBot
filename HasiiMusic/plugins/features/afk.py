# ==============================================================================
# afk.py - AFK Feature
# ==============================================================================
# /afk [reason]  — AFK mark karo ya toggle karo
# Auto: jab AFK user message bheje → wapas aa gaya notify karo
# Auto: jab koi AFK user ko mention/reply kare → AFK batao
# ==============================================================================

import time
from pyrogram import filters, types
from HasiiMusic import app, db


_afk_cache: dict[int, dict] = {}


async def _set_afk(user_id: int, reason: str):
    data = {"reason": reason, "since": time.time()}
    _afk_cache[user_id] = data
    await db.mongo.HasiiTune.afk.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, **data}},
        upsert=True,
    )


async def _del_afk(user_id: int):
    _afk_cache.pop(user_id, None)
    await db.mongo.HasiiTune.afk.delete_one({"user_id": user_id})


async def _is_afk(user_id: int) -> dict | None:
    if user_id in _afk_cache:
        return _afk_cache[user_id]
    doc = await db.mongo.HasiiTune.afk.find_one({"user_id": user_id})
    if doc:
        entry = {"reason": doc.get("reason", ""), "since": doc.get("since", time.time())}
        _afk_cache[user_id] = entry
        return entry
    return None


def _fmt_time(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"


@app.on_message(filters.command("afk") & ~filters.private)
async def afk_cmd(_, message: types.Message):
    if not message.from_user:
        return
    try:
        await message.delete()
    except Exception:
        pass

    user = message.from_user
    reason = " ".join(message.command[1:]) if len(message.command) > 1 else ""

    if await _is_afk(user.id):
        await _del_afk(user.id)
        return await message.reply_text(
            f"<blockquote>✅ {user.mention} ɪꜱ ɴᴏ ʟᴏɴɢᴇʀ ᴀꜰᴋ!</blockquote>"
        )

    await _set_afk(user.id, reason)
    text = f"<blockquote>😴 {user.mention} ɪꜱ ɴᴏᴡ ᴀꜰᴋ"
    if reason:
        text += f"\n📝 ʀᴇᴀꜱᴏɴ: {reason}"
    text += "</blockquote>"
    await message.reply_text(text)


@app.on_message(filters.group & ~filters.service, group=10)
async def afk_watcher(_, message: types.Message):
    if not message.from_user:
        return
    user = message.from_user

    if message.text and message.text.strip().startswith("/afk"):
        return

    afk_data = await _is_afk(user.id)
    if afk_data:
        gone = time.time() - afk_data.get("since", time.time())
        await _del_afk(user.id)
        try:
            await message.reply_text(
                f"<blockquote>👋 {user.mention} ɪꜱ ʙᴀᴄᴋ!\n"
                f"⏱️ ᴡᴀꜱ ᴀᴡᴀʏ ꜰᴏʀ: {_fmt_time(gone)}</blockquote>",
                disable_notification=True,
            )
        except Exception:
            pass
        return

    mentioned_ids: list[int] = []
    if message.entities:
        for ent in message.entities:
            if ent.type.name == "MENTION" and message.text:
                uname = message.text[ent.offset + 1: ent.offset + ent.length]
                try:
                    u = await app.get_users(uname)
                    mentioned_ids.append(u.id)
                except Exception:
                    pass
            elif ent.type.name == "TEXT_MENTION" and ent.user:
                mentioned_ids.append(ent.user.id)

    if message.reply_to_message and message.reply_to_message.from_user:
        mentioned_ids.append(message.reply_to_message.from_user.id)

    for uid in set(mentioned_ids):
        if uid == user.id:
            continue
        afk_info = await _is_afk(uid)
        if not afk_info:
            continue
        gone = time.time() - afk_info.get("since", time.time())
        try:
            u = await app.get_users(uid)
            reason_line = f"\n📝 ʀᴇᴀꜱᴏɴ: {afk_info['reason']}" if afk_info.get("reason") else ""
            await message.reply_text(
                f"<blockquote>😴 {u.mention} ɪꜱ ᴀꜰᴋ ʀɪɢʜᴛ ɴᴏᴡ{reason_line}\n"
                f"⏱️ ᴀᴡᴀʏ ꜰᴏʀ: {_fmt_time(gone)}</blockquote>",
                disable_notification=True,
            )
        except Exception:
            pass
