"""
GIF Manager — v5 FINAL
Place at: HasiiMusic/helpers/gif_manager.py
"""

import random
import time

from pymongo import MongoClient as PyMongoClient

try:
    from HasiiMusic.core.mongo import mongodb as _db
    gif_col = _db["gif_configs"]
except Exception:
    import os
    _c = PyMongoClient(os.getenv("MONGO_DB_URI", "mongodb://localhost:27017"))
    gif_col = _c["HasiiMusicBot"]["gif_configs"]


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
        {"file_id": "CgACAgQAAxkBAAFK1XtqF9_2tJ3gO-M4s5maiJUEhyOj8QACYAYAArVNxVPwrkrEYMP32DsE", "name": "afk-sleeping-1"},
        {"file_id": "CgACAgQAAxkBAAFK1X1qF9_9eF2EuPslGxXRc_IJjJakuwACcgoAAsxW1VF_E0ajtS9OWDsE", "name": "afk-sleeping-2"},
        {"file_id": "CgACAgQAAxkBAAFK1X9qF-AEMI7JIAND7ETKRFm39cuMOgAC3QUAArsSfFKCBG-3ncRIijsE", "name": "afk-sleeping-3"},
    ],
    "welcome": [
        {"file_id": "CgACAgQAAxkBAAFK9N9qGYmPGkAqgIeRQOqAHLX8hJVXtQACjwoAAjIS1FMU4limPm1u6TsE", "name": "welcome-wave-1"},
        {"file_id": "CgACAgQAAxkBAAFK9NtqGYltnBtoCk7VxU3EJ300kL99uwAClgoAAhFTVFGKWgZh40VeIjsE", "name": "welcome-cheer-1"},
    ],
    "start": [
        {"file_id": "CgACAgQAAxkBAAFK9N9qGYmPGkAqgIeRQOqAHLX8hJVXtQACjwoAAjIS1FMU4limPm1u6TsE", "name": "start-default"},
    ],
    "play": [
        {"file_id": "CAACAgUAAxkBAAFK2l9qGCwP-906O81HLo8pxYoR7SdStAACXyAAAkfhyVSX1A2fYeap8DsE", "name": "play-sticker-1"},
        {"file_id": "CAACAgUAAxkBAAFK2mFqGCwUFZFdBYmV-ubGzdQV6Z0PAwACySAAAiY8wFQqWC8co8TsbjsE", "name": "play-sticker-2"},
    ],
    "gmtag":  [],
    "gntag":  [],
    "gdtag":  [],
    "gevtag": [],
    "gbdtag": [],
}


def _get_doc(gif_type: str) -> dict:
    try:
        return gif_col.find_one({"type": gif_type}) or {}
    except Exception:
        return {}


def get_gifs(gif_type: str) -> list:
    doc = _get_doc(gif_type)
    custom = doc.get("gifs", [])
    return custom if custom else DEFAULTS.get(gif_type, [])


def get_random_gif(gif_type: str):
    gifs = get_gifs(gif_type)
    return random.choice(gifs)["file_id"] if gifs else None


def add_gif(gif_type: str, file_id: str, name: str) -> bool:
    try:
        doc = _get_doc(gif_type)
        gifs = doc.get("gifs", [])
        if any(g["file_id"] == file_id for g in gifs):
            return False
        gifs.append({"file_id": file_id, "name": name, "added_at": int(time.time())})
        gif_col.update_one({"type": gif_type}, {"$set": {"gifs": gifs}}, upsert=True)
        return True
    except Exception:
        return False


def remove_gif(gif_type: str, index: int):
    try:
        doc = _get_doc(gif_type)
        gifs = doc.get("gifs", [])
        if not gifs:
            return None
        idx = index - 1
        if idx < 0 or idx >= len(gifs):
            return None
        removed = gifs.pop(idx)
        gif_col.update_one({"type": gif_type}, {"$set": {"gifs": gifs}}, upsert=True)
        return removed
    except Exception:
        return None


def list_gifs_text(gif_type: str) -> str:
    try:
        doc = _get_doc(gif_type)
        custom = doc.get("gifs", [])
    except Exception:
        custom = []
    using_default = not custom
    gifs = custom if custom else DEFAULTS.get(gif_type, [])
    if not gifs:
        return (
            f"<blockquote>📭 <b>{gif_type.upper()} GIFs</b>\n\nNo GIFs set yet!\n\n"
            f"Reply to a GIF and use <code>/set{gif_type}gif</code> to add one.</blockquote>"
        )
    source = "default" if using_default else "custom"
    lines = [f"<blockquote>🎬 <b>{gif_type.upper()} GIFs</b> ({source}):\n"]
    for i, g in enumerate(gifs, 1):
        name = g.get("name", "unnamed")
        fid_short = g["file_id"][:22] + "..."
        lines.append(f"<b>{i}.</b> {name}\n   <code>{fid_short}</code>")
    lines.append(f"\n📊 Total: <b>{len(gifs)}</b>")
    if using_default:
        lines.append("\nℹ️ <i>Using defaults — set your own GIFs to replace them.</i>")
    lines.append("</blockquote>")
    return "\n".join(lines)


def _is_owner_or_sudo(user_id: int) -> bool:
    try:
        from HasiiMusic import config, app as _app
        for attr in ("OWNER_ID", "OWNER", "BOT_OWNER"):
            val = getattr(config, attr, None)
            if val and int(val) == user_id:
                return True
        if hasattr(_app, "sudoers") and user_id in _app.sudoers:
            return True
    except Exception:
        pass
    return False


async def is_owner_sudo_or_admin(client, chat_id: int, user_id: int) -> bool:
    if _is_owner_or_sudo(user_id):
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


def extract_file_id(message):
    if message.sticker:
        return message.sticker.file_id, message.sticker.emoji or "sticker"
    if message.animation:
        return message.animation.file_id, message.animation.file_name or "animation"
    if message.video:
        return message.video.file_id, message.video.file_name or "video"
    if message.document and message.document.mime_type and "video" in message.document.mime_type:
        return message.document.file_id, message.document.file_name or "document"
    return None, None


def register_gif_commands(app_instance, gif_type: str, cmd_prefix: str):
    from pyrogram import enums, filters

    set_cmd  = f"set{cmd_prefix}gif"
    rm_cmd   = f"rm{cmd_prefix}gif"
    list_cmd = f"list{cmd_prefix}gif"

    @app_instance.on_message(filters.command(set_cmd))
    async def _set_gif(client, message):
        if not message.from_user:
            return
        if not await is_owner_sudo_or_admin(client, message.chat.id, message.from_user.id):
            return await message.reply(
                "<blockquote>❌ Only the owner, sudo users, or admins can manage GIFs.</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        src = message.reply_to_message or message
        file_id, fname = extract_file_id(src)
        if not file_id:
            return await message.reply(
                f"<blockquote>❌ <b>No GIF or sticker found!</b>\n\nReply to a GIF or sticker with <code>/{set_cmd}</code></blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        custom_name = " ".join(message.command[1:]).strip() if len(message.command) > 1 else fname
        added = add_gif(gif_type, file_id, custom_name)
        total = len(get_gifs(gif_type))
        if added:
            await message.reply(
                f"<blockquote>✅ <b>{gif_type.upper()} GIF added!</b>\n\n📛 Name: <b>{custom_name}</b>\n📊 Total: <b>{total}</b>\n\nUse <code>/{list_cmd}</code> to see all.</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply(
                "<blockquote>⚠️ This GIF is already in the pool!</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )

    @app_instance.on_message(filters.command(rm_cmd))
    async def _rm_gif(client, message):
        if not message.from_user:
            return
        if not await is_owner_sudo_or_admin(client, message.chat.id, message.from_user.id):
            return await message.reply(
                "<blockquote>❌ Only the owner, sudo users, or admins can manage GIFs.</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        if len(message.command) < 2:
            return await message.reply(
                f"<blockquote>❌ Usage: <code>/{rm_cmd} &lt;number&gt;</code>\nUse <code>/{list_cmd}</code> to see numbers.</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        try:
            idx = int(message.command[1])
        except ValueError:
            return await message.reply(
                f"<blockquote>❌ Invalid number! Example: <code>/{rm_cmd} 2</code></blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        removed = remove_gif(gif_type, idx)
        if removed:
            remaining = len(get_gifs(gif_type))
            await message.reply(
                f"<blockquote>🗑 <b>GIF removed!</b>\n\n📛 Name: <b>{removed.get('name', 'unnamed')}</b>\n📊 Remaining: <b>{remaining}</b></blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply(
                f"<blockquote>❌ No GIF at position {idx}.\nUse <code>/{list_cmd}</code> to see valid numbers.</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )

    @app_instance.on_message(filters.command(list_cmd))
    async def _list_gif(client, message):
        text = list_gifs_text(gif_type)
        await message.reply(text, parse_mode=enums.ParseMode.HTML)
