"""
GIF Manager — Shared helper for all plugins
Stores GIFs per type in MongoDB. Add/remove/list from bot directly.
Types: "couple", "afk", "welcome", "start", "ping"
"""

from pymongo import MongoClient as PyMongoClient
import time

try:
    from HasiiMusic.core.mongo import mongodb as _db
    gif_col = _db["gif_configs"]
except ImportError:
    import os
    _c = PyMongoClient(os.getenv("MONGO_DB_URI", "mongodb://localhost:27017"))
    gif_col = _c["HasiiMusicBot"]["gif_configs"]

# ── Default fallback GIFs (used if owner hasn't set any) ──────────────────────
DEFAULTS = {
    "couple": [
        {"file_id": "CgACAgUAAxkBAAFK1WRqF97lOizVVHm5_u0D8fXY3W-tAANCKgACBOwYVJ1ADjmP2ejnOwQ",   "name": "couple-1"},
        {"file_id": "CgACAgUAAxkBAAFK1WZqF97vaBAbc9D5AAEJ3R5efIwkEpEAAkMqAAIE7BhUPG_GhsQDS7g7BA", "name": "couple-2"},
        {"file_id": "CgACAgUAAxkBAAFK1WlqF973_CEJe0Sh7KPas3ksnWrz4wACRCoAAgTsGFR4bGRskjrbxDsE",   "name": "couple-3"},
        {"file_id": "CgACAgUAAxkBAAFK1W9qF98jijDe57jE002MuXlrYhU3EwACQSoAAgTsGFRRl8lSCLWsFDsE",   "name": "couple-4"},
        {"file_id": "CgACAgQAAxkBAAFK9NVqGYk7xGGp2pAGKupttLxHLImdNAACywgAAlbJrFHKM99F2lJZNjsE",   "name": "couple-5"},
        {"file_id": "CgACAgQAAxkBAAFK9NdqGYlJRLjZxUlz6jec9SLLVAVZnQACIAoAApdj3FK7a0fitBb2rjsE",   "name": "couple-6"},
        {"file_id": "CgACAgQAAxkBAAFK9NtqGYltnBtoCk7VxU3EJ300kL99uwAClgoAAhFTVFGKWgZh40VeIjsE",   "name": "couple-7"},
        {"file_id": "CgACAgQAAxkBAAFK9OpqGYmyFoqnLKhJv0SphjfTUPupawAC4gQAAhZQHFHHpA-xsiUtfjsE",   "name": "couple-8"},
    ],
    "afk": [
        {"file_id": "CgACAgQAAxkBAAFK1XtqF9_2tJ3gO-M4s5maiJUEhyOj8QACYAYAArVNxVPwrkrEYMP32DsE", "name": "meryl-sleeping"},
        {"file_id": "CgACAgQAAxkBAAFK1X1qF9_9eF2EuPslGxXRc_IJjJakuwACcgoAAsxW1VF_E0ajtS9OWDsE", "name": "agleia-afk"},
        {"file_id": "CgACAgQAAxkBAAFK1X9qF-AEMI7JIAND7ETKRFm39cuMOgAC3QUAArsSfFKCBG-3ncRIijsE", "name": "nemesis-sleeping"},
    ],
    "welcome": [
        {"file_id": "CgACAgUAAxkBAAFK1WRqF97lOizVVHm5_u0D8fXY3W-tAANCKgACBOwYVJ1ADjmP2ejnOwQ",   "name": "welcome-1"},
        {"file_id": "CgACAgUAAxkBAAFK1WZqF97vaBAbc9D5AAEJ3R5efIwkEpEAAkMqAAIE7BhUPG_GhsQDS7g7BA", "name": "welcome-2"},
        {"file_id": "CgACAgUAAxkBAAFK1WlqF973_CEJe0Sh7KPas3ksnWrz4wACRCoAAgTsGFR4bGRskjrbxDsE",   "name": "welcome-3"},
        {"file_id": "CgACAgUAAxkBAAFK1W9qF98jijDe57jE002MuXlrYhU3EwACQSoAAgTsGFRRl8lSCLWsFDsE",   "name": "welcome-4"},
    ],
    "start": [
        {"file_id": "CgACAgQAAxkBAAFK9N9qGYmPGkAqgIeRQOqAHLX8hJVXtQACjwoAAjIS1FMU4limPm1u6TsE", "name": "mint-nikke"},
    ],
    "ping": [
        {"file_id": "CgACAgQAAxkBAAFK9NVqGYk7xGGp2pAGKupttLxHLImdNAACywgAAlbJrFHKM99F2lJZNjsE", "name": "ping-default"},
    ],
}


def _get_doc(gif_type: str) -> dict:
    return gif_col.find_one({"type": gif_type}) or {}


def get_gifs(gif_type: str) -> list:
    """Return list of {file_id, name} dicts. Falls back to defaults if none set."""
    doc = _get_doc(gif_type)
    gifs = doc.get("gifs", [])
    return gifs if gifs else DEFAULTS.get(gif_type, [])


def get_random_gif(gif_type: str):
    """Return a random file_id for this type."""
    import random
    gifs = get_gifs(gif_type)
    return random.choice(gifs)["file_id"] if gifs else None


def add_gif(gif_type: str, file_id: str, name: str) -> bool:
    """Add a GIF. Returns False if already exists."""
    doc = _get_doc(gif_type)
    gifs = doc.get("gifs", [])
    if any(g["file_id"] == file_id for g in gifs):
        return False
    gifs.append({"file_id": file_id, "name": name, "added_at": int(time.time())})
    gif_col.update_one(
        {"type": gif_type},
        {"$set": {"gifs": gifs}},
        upsert=True
    )
    return True


def remove_gif(gif_type: str, index: int):
    """Remove GIF by 1-based index. Returns removed entry or None."""
    doc = _get_doc(gif_type)
    gifs = doc.get("gifs", [])
    if not gifs:
        return None
    idx = index - 1
    if idx < 0 or idx >= len(gifs):
        return None
    removed = gifs.pop(idx)
    gif_col.update_one(
        {"type": gif_type},
        {"$set": {"gifs": gifs}},
        upsert=True
    )
    return removed


def list_gifs_text(gif_type: str) -> str:
    """Return formatted blockquote text list of GIFs."""
    doc = _get_doc(gif_type)
    custom = doc.get("gifs", [])
    using_default = not custom
    gifs = custom if custom else DEFAULTS.get(gif_type, [])

    if not gifs:
        return f"<blockquote>❌ <b>{gif_type.upper()} GIFs:</b> Koi GIF set nahi hai.</blockquote>"

    lines = [f"<blockquote>🎬 <b>{gif_type.upper()} GIFs</b> {'(default)' if using_default else '(custom)'}:\n"]
    for i, g in enumerate(gifs, 1):
        name = g.get("name", "unnamed")
        fid_short = g["file_id"][:20] + "..."
        lines.append(f"<b>{i}.</b> {name}\n   <code>{fid_short}</code>")

    lines.append(f"\n📊 Total: <b>{len(gifs)}</b>")
    if using_default:
        lines.append("ℹ️ <i>Custom GIFs nahi hain — defaults use ho rahe hain</i>")
    lines.append("</blockquote>")

    return "\n".join(lines)


# ── Owner/sudo check helper ───────────────────────────────────────────────────
def is_owner_or_sudo(user_id: int) -> bool:
    try:
        from HasiiMusic import config, app as _app
        if user_id == int(getattr(config, "OWNER_ID", 0)):
            return True
        if hasattr(_app, "sudoers") and user_id in _app.sudoers:
            return True
    except Exception:
        pass
    return False


async def is_owner_sudo_or_admin(client, chat_id: int, user_id: int) -> bool:
    """Check if user is owner, sudo, or group admin."""
    if is_owner_or_sudo(user_id):
        return True
    try:
        from pyrogram import enums
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


# ── Extract file_id from a message (animation/video/document) ─────────────────
def extract_file_id(message):
    """Returns (file_id, name) from a message that has a GIF/animation."""
    if message.animation:
        return message.animation.file_id, message.animation.file_name or "animation"
    if message.video:
        return message.video.file_id, message.video.file_name or "video"
    if message.document and message.document.mime_type and "video" in message.document.mime_type:
        return message.document.file_id, message.document.file_name or "document"
    return None, None


# ── Shared command builder — call this in each plugin ────────────────────────
def register_gif_commands(app_instance, gif_type: str, cmd_prefix: str):
    """
    Registers /set{prefix}gif, /rm{prefix}gif, /list{prefix}gif
    on the given Pyrogram app instance.
    """
    from pyrogram import filters

    set_cmd  = f"set{cmd_prefix}gif"
    rm_cmd   = f"rm{cmd_prefix}gif"
    list_cmd = f"list{cmd_prefix}gif"

    @app_instance.on_message(filters.command(set_cmd))
    async def _set_gif(client, message):
        if not await is_owner_sudo_or_admin(client, message.chat.id, message.from_user.id):
            return await message.reply(
                "<blockquote>❌ Sirf owner/sudo/admin yeh kar sakte hain.</blockquote>",
                parse_mode="html"
            )

        src = message.reply_to_message or message
        file_id, fname = extract_file_id(src)

        if not file_id:
            return await message.reply(
                f"<blockquote>"
                f"❌ <b>GIF nahi mili!</b>\n\n"
                f"Kisi GIF ko reply karke <code>/{set_cmd}</code> likho\n"
                f"Ya ek custom naam bhi de sakte ho:\n"
                f"<code>/{set_cmd} meri-gif</code>"
                f"</blockquote>",
                parse_mode="html"
            )

        custom_name = " ".join(message.command[1:]).strip() if len(message.command) > 1 else fname

        added = add_gif(gif_type, file_id, custom_name)
        gifs = get_gifs(gif_type)

        if added:
            await message.reply(
                f"<blockquote>"
                f"✅ <b>{gif_type.upper()} GIF add ho gayi!</b>\n\n"
                f"📛 Naam: <b>{custom_name}</b>\n"
                f"📊 Total ab: <b>{len(gifs)}</b> GIFs\n\n"
                f"<code>/{list_cmd}</code> se list dekho"
                f"</blockquote>",
                parse_mode="html"
            )
        else:
            await message.reply(
                "<blockquote>⚠️ Yeh GIF pehle se list mein hai!</blockquote>",
                parse_mode="html"
            )

    @app_instance.on_message(filters.command(rm_cmd))
    async def _rm_gif(client, message):
        if not await is_owner_sudo_or_admin(client, message.chat.id, message.from_user.id):
            return await message.reply(
                "<blockquote>❌ Sirf owner/sudo/admin yeh kar sakte hain.</blockquote>",
                parse_mode="html"
            )

        if len(message.command) < 2:
            return await message.reply(
                f"<blockquote>"
                f"❌ Number do!\n"
                f"Usage: <code>/{rm_cmd} &lt;number&gt;</code>\n"
                f"<code>/{list_cmd}</code> se numbers dekho"
                f"</blockquote>",
                parse_mode="html"
            )

        try:
            idx = int(message.command[1])
        except ValueError:
            return await message.reply(
                f"<blockquote>❌ Valid number do! Example: <code>/{rm_cmd} 2</code></blockquote>",
                parse_mode="html"
            )

        removed = remove_gif(gif_type, idx)
        if removed:
            remaining = get_gifs(gif_type)
            await message.reply(
                f"<blockquote>"
                f"🗑 <b>GIF remove ho gayi!</b>\n\n"
                f"📛 Naam: <b>{removed.get('name', 'unnamed')}</b>\n"
                f"📊 Bacha: <b>{len(remaining)}</b> GIFs"
                f"</blockquote>",
                parse_mode="html"
            )
        else:
            await message.reply(
                f"<blockquote>"
                f"❌ Number {idx} exist nahi karta.\n"
                f"<code>/{list_cmd}</code> se sahi number dekho"
                f"</blockquote>",
                parse_mode="html"
            )

    @app_instance.on_message(filters.command(list_cmd))
    async def _list_gif(client, message):
        text = list_gifs_text(gif_type)
        await message.reply(text, parse_mode="html")
