import time
from pyrogram import filters, types
from HasiiMusic import app

_afk_users: dict = {}


def _format_time(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    elif seconds < 86400:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"
    else:
        d = seconds // 86400
        h = (seconds % 86400) // 3600
        return f"{d}d {h}h"


@app.on_message(filters.command(["afk"]) & filters.group)
async def set_afk(_, m: types.Message):
    user = m.from_user
    reason = " ".join(m.command[1:]) if len(m.command) > 1 else "Koi reason nahi"
    _afk_users[user.id] = {
        "reason": reason,
        "time": int(time.time()),
        "name": user.first_name,
    }
    try:
        await m.delete()
    except Exception:
        pass
    await m.reply_text(
        f"<blockquote><b>😴 {user.mention} AFK Ho Gaya!</b></blockquote>\n\n"
        f"<blockquote>Reason: <b>{reason}</b>\n"
        f"Time: <b>Abhi</b></blockquote>"
    )


@app.on_message(filters.command(["unafk"]) & filters.group)
async def unset_afk(_, m: types.Message):
    user = m.from_user
    if user.id in _afk_users:
        afk_data = _afk_users.pop(user.id)
        gone_for = int(time.time()) - afk_data["time"]
        await m.reply_text(
            f"<blockquote><b>👋 {user.mention} Wapas Aa Gaya!</b></blockquote>\n\n"
            f"<blockquote>Gone for: <b>{_format_time(gone_for)}</b></blockquote>"
        )
    else:
        await m.reply_text("<blockquote><b>Aap AFK nahi the!</b></blockquote>")


@app.on_message(filters.group & ~filters.bot & ~filters.command([]))
async def afk_watcher(_, m: types.Message):
    if not m.from_user:
        return

    # Remove AFK if user sends a message
    user_id = m.from_user.id
    if user_id in _afk_users and not (m.text and m.text.startswith("/")):
        afk_data = _afk_users.pop(user_id)
        gone_for = int(time.time()) - afk_data["time"]
        try:
            await m.reply_text(
                f"<blockquote><b>👋 {m.from_user.mention} Wapas Aa Gaya!</b></blockquote>\n\n"
                f"<blockquote>Gone for: <b>{_format_time(gone_for)}</b>\n"
                f"Reason tha: <b>{afk_data['reason']}</b></blockquote>"
            )
        except Exception:
            pass
        return

    # Check if someone mentioned an AFK user
    mentioned_ids = []
    if m.entities:
        for entity in m.entities:
            if entity.type.name == "MENTION":
                username = m.text[entity.offset + 1: entity.offset + entity.length]
                try:
                    u = await app.get_users(username)
                    mentioned_ids.append(u.id)
                except Exception:
                    pass
            elif entity.type.name == "TEXT_MENTION" and entity.user:
                mentioned_ids.append(entity.user.id)

    if m.reply_to_message and m.reply_to_message.from_user:
        mentioned_ids.append(m.reply_to_message.from_user.id)

    for uid in set(mentioned_ids):
        if uid in _afk_users:
            afk_data = _afk_users[uid]
            gone_for = int(time.time()) - afk_data["time"]
            try:
                await m.reply_text(
                    f"<blockquote><b>😴 {afk_data['name']} Abhi AFK Hai!</b></blockquote>\n\n"
                    f"<blockquote>Reason: <b>{afk_data['reason']}</b>\n"
                    f"Since: <b>{_format_time(gone_for)} pehle</b></blockquote>"
                )
            except Exception:
                pass
