"""
GIF Manager — Full Version v2
Place at: HasiiMusic/helpers/gif_manager.py
"""

import asyncio
import random

from pyrogram import enums, filters

_GIFS: dict[str, list[str]] = {

    "play": [
        "https://media.tenor.com/aD4NaQHNBIsAAAAC/music-anime.gif",
        "https://media.tenor.com/YMWHuiN3EsQAAAAC/anime-music.gif",
        "https://media.tenor.com/CqtFRPUq2KEAAAAC/anime-dancing.gif",
        "https://media.tenor.com/Y6jq3HqX7joAAAAC/music-playing.gif",
        "https://media.tenor.com/dM3tjKF4FNAAAAAC/anime-headphones.gif",
        "https://media.tenor.com/LxJJFB0XKTEAAAAC/anime-music-vibes.gif",
    ],

    "afk": [
        "https://media.tenor.com/RZmMzm8H9HIAAAAC/anime-sleeping.gif",
        "https://media.tenor.com/3b2mfUmC4GEAAAAC/sleeping-anime.gif",
        "https://media.tenor.com/jBE1gCM6qZkAAAAC/sleep-anime-girl.gif",
        "https://media.tenor.com/7T1HdqX27TUAAAAC/anime-sleep.gif",
        "https://media.tenor.com/8IXpFZnFd8EAAAAC/sleeping-zzz.gif",
        "https://media.tenor.com/Mj5JCQjHEicAAAAC/sleeping-girl-anime.gif",
    ],

    "welcome": [
        "https://media.tenor.com/hzFoP4RoRIYAAAAC/anime-wave.gif",
        "https://media.tenor.com/Vj4Mh_DpiLYAAAAC/hi-hello.gif",
        "https://media.tenor.com/kj5JaHHN5KYAAAAC/anime-hello.gif",
        "https://media.tenor.com/ZCDpOiMb7LAAAAAC/welcome-anime.gif",
        "https://media.tenor.com/0tvoQar0alsAAAAC/hello-wave.gif",
        "https://media.tenor.com/uFzNvBn8BYYAAAAC/waving-hi.gif",
    ],

    "goodbye": [
        "https://media.tenor.com/X_3Jp0TlgsYAAAAC/bye-anime.gif",
        "https://media.tenor.com/4dIPYW0Y3XAAAAAC/goodbye-anime.gif",
        "https://media.tenor.com/H_H3RNPB5KEAAAAC/bye-bye-anime.gif",
        "https://media.tenor.com/dghQO8s6GakAAAAC/anime-goodbye.gif",
    ],

    "couple": [
        "https://media.tenor.com/B-iaTsFenUoAAAAC/anime-couple.gif",
        "https://media.tenor.com/Ld-cDzuBuKMAAAAC/anime-love.gif",
        "https://media.tenor.com/8U0_pIrTbPoAAAAC/anime-couple-love.gif",
        "https://media.tenor.com/T9b5qsMHWrUAAAAC/love-anime.gif",
        "https://media.tenor.com/OmBcFUMlKAEAAAAC/anime-kiss.gif",
        "https://media.tenor.com/uIkUi_khlbkAAAAC/anime-hug.gif",
    ],

    "tagall": [
        "https://media.tenor.com/fY8iU9gBSsIAAAAC/anime-attention.gif",
        "https://media.tenor.com/5hGlkFj6MBoAAAAC/notification-alert.gif",
        "https://media.tenor.com/9j1FaTHCKJwAAAAC/anime-announcement.gif",
        "https://media.tenor.com/kG2aSAJhipgAAAAC/anime-calling.gif",
    ],

    "tagadmins": [
        "https://media.tenor.com/Qlg5KUHLf5UAAAAC/anime-serious.gif",
        "https://media.tenor.com/QGbJTSiGjBYAAAAC/anime-alert.gif",
        "https://media.tenor.com/eXSk3VVDGKUAAAAC/anime-police.gif",
    ],

    "roasttag": [
        "https://media.tenor.com/PmV8wJbdZOkAAAAC/anime-fire.gif",
        "https://media.tenor.com/lz_-mjPLEpYAAAAC/anime-burn.gif",
        "https://media.tenor.com/jk2h5lnJVPkAAAAC/fire-anime.gif",
    ],

    "gmtag": [
        "https://media.tenor.com/tUv8V9cHFRoAAAAC/good-morning-anime.gif",
        "https://media.tenor.com/N3HZYC0hG5YAAAAC/anime-good-morning.gif",
        "https://media.tenor.com/uRKRzGV_KsAAAAC/morning-coffee.gif",
        "https://media.tenor.com/qST5QXNLPOMAAAAC/good-morning.gif",
    ],

    "gntag": [
        "https://media.tenor.com/4tBzFqjPBikAAAAC/good-night-anime.gif",
        "https://media.tenor.com/k1f7iBMCo6IAAAAC/anime-good-night.gif",
        "https://media.tenor.com/AUNhkFJ7N-cAAAAC/night-sleep.gif",
        "https://media.tenor.com/mJvuyq5Z0AQAAAAC/good-night.gif",
    ],

    "gdtag": [
        "https://media.tenor.com/CWaBheLuqf4AAAAC/good-afternoon-anime.gif",
        "https://media.tenor.com/uDN7XFCUQ7AAAAAC/good-afternoon.gif",
    ],

    "gevtag": [
        "https://media.tenor.com/vRiPTl2GLHMAAAAC/good-evening-anime.gif",
        "https://media.tenor.com/lh0wuwEuehMAAAAC/good-evening.gif",
    ],

    "gbdtag": [
        "https://media.tenor.com/gJB41QnTGm8AAAAC/anime-birthday.gif",
        "https://media.tenor.com/Bv_uMzWA-scAAAAC/happy-birthday-anime.gif",
        "https://media.tenor.com/iF0s2xA0_MoAAAAC/birthday-cake.gif",
    ],
}

_custom: dict[str, list[dict]] = {}


# ── Core CRUD ─────────────────────────────────────────────────────────────────

def get_random_gif(gif_type: str) -> str | None:
    custom = _custom.get(gif_type, [])
    if custom:
        return random.choice(custom)["id"]
    pool = _GIFS.get(gif_type, [])
    return random.choice(pool) if pool else None


def get_gifs(gif_type: str) -> list[dict]:
    return list(_custom.get(gif_type, []))


def add_gif(gif_type: str, file_id: str, name: str = "") -> int:
    if gif_type not in _custom:
        _custom[gif_type] = []
    _custom[gif_type].append({"id": file_id, "name": name or file_id[:20]})
    return len(_custom[gif_type])


def remove_gif(gif_type: str, index: int) -> bool:
    lst = _custom.get(gif_type, [])
    idx = index - 1
    if 0 <= idx < len(lst):
        lst.pop(idx)
        return True
    return False


def list_gifs_text(gif_type: str) -> str:
    custom = _custom.get(gif_type, [])
    defaults = _GIFS.get(gif_type, [])
    lines = [f"<blockquote><b>🎞 GIFs — {gif_type}</b>\n━━━━━━━━━━━━━━━━━━"]
    if custom:
        lines.append(f"\n<b>✨ Custom ({len(custom)}):</b>")
        for i, g in enumerate(custom, 1):
            lines.append(f"  {i}. {g['name'] or 'unnamed'}")
    else:
        lines.append("\n<i>No custom GIFs set.</i>")
    lines.append(f"\n<b>📦 Default pool:</b> {len(defaults)} GIFs")
    lines.append("</blockquote>")
    return "\n".join(lines)


def extract_file_id(message) -> str | None:
    if message is None:
        return None
    if message.sticker:
        return message.sticker.file_id
    if message.animation:
        return message.animation.file_id
    if message.video:
        return message.video.file_id
    if message.photo:
        return message.photo.file_id
    if message.document:
        mime = getattr(message.document, "mime_type", "") or ""
        if "gif" in mime or "video" in mime or "image" in mime:
            return message.document.file_id
    return None


def list_gif_types() -> list[str]:
    return sorted(_GIFS.keys())


# ── Auth ──────────────────────────────────────────────────────────────────────

async def is_owner_or_sudo(user_id: int) -> bool:
    try:
        from HasiiMusic import OWNER_ID
        owners = [int(x) for x in OWNER_ID] if isinstance(OWNER_ID, (list, tuple)) else [int(OWNER_ID)]
        if user_id in owners:
            return True
    except Exception:
        pass
    try:
        from HasiiMusic import SUDO_USERS
        if SUDO_USERS:
            sudos = [int(x) for x in SUDO_USERS] if isinstance(SUDO_USERS, (list, tuple, set)) else [int(SUDO_USERS)]
            if user_id in sudos:
                return True
    except Exception:
        pass
    return False


# ── Register GIF Commands ─────────────────────────────────────────────────────

def register_gif_commands(app, gif_type: str, prefix: str):
    """
    Registers owner/sudo GIF commands:
      /set<prefix>gif [name]  — reply to GIF/sticker to add
      /rm<prefix>gif <n>      — remove by number
      /list<prefix>gif        — list all

    Example: register_gif_commands(app, "play", "play")
      → /setplaygif  /rmplaygif  /listplaygif
    """

    set_cmd  = f"set{prefix}gif"
    rm_cmd   = f"rm{prefix}gif"
    list_cmd = f"list{prefix}gif"

    @app.on_message(filters.command(set_cmd))
    async def _set_gif(_, message):
        if not message.from_user:
            return
        if not await is_owner_or_sudo(message.from_user.id):
            s = await message.reply(
                "<blockquote>🚫 Only owner/sudo can manage GIFs.</blockquote>",
                parse_mode=enums.ParseMode.HTML,
            )
            asyncio.create_task(_auto_del(s, 10))
            return
        file_id = extract_file_id(message.reply_to_message)
        if not file_id:
            s = await message.reply(
                f"<blockquote>⚠️ GIF/sticker ko reply karke /{set_cmd} [name] bhejo.</blockquote>",
                parse_mode=enums.ParseMode.HTML,
            )
            asyncio.create_task(_auto_del(s, 15))
            return
        name = " ".join(message.command[1:]).strip() if len(message.command) > 1 else ""
        count = add_gif(gif_type, file_id, name)
        s = await message.reply(
            f"<blockquote>✅ GIF added for <b>{gif_type}</b>!\n📊 Total: <b>{count}</b></blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_del(s, 20))

    @app.on_message(filters.command(rm_cmd))
    async def _rm_gif(_, message):
        if not message.from_user:
            return
        if not await is_owner_or_sudo(message.from_user.id):
            s = await message.reply(
                "<blockquote>🚫 Only owner/sudo can manage GIFs.</blockquote>",
                parse_mode=enums.ParseMode.HTML,
            )
            asyncio.create_task(_auto_del(s, 10))
            return
        if len(message.command) < 2 or not message.command[1].isdigit():
            s = await message.reply(
                f"<blockquote>⚠️ Usage: /{rm_cmd} &lt;number&gt;\nUse /{list_cmd} to see numbers.</blockquote>",
                parse_mode=enums.ParseMode.HTML,
            )
            asyncio.create_task(_auto_del(s, 15))
            return
        idx = int(message.command[1])
        if remove_gif(gif_type, idx):
            s = await message.reply(
                f"<blockquote>🗑 GIF #{idx} removed from <b>{gif_type}</b>.</blockquote>",
                parse_mode=enums.ParseMode.HTML,
            )
        else:
            s = await message.reply(
                f"<blockquote>❌ No GIF at #{idx}. Use /{list_cmd} to check.</blockquote>",
                parse_mode=enums.ParseMode.HTML,
            )
        asyncio.create_task(_auto_del(s, 15))

    @app.on_message(filters.command(list_cmd))
    async def _list_gifs(_, message):
        if not message.from_user:
            return
        if not await is_owner_or_sudo(message.from_user.id):
            s = await message.reply(
                "<blockquote>🚫 Only owner/sudo can manage GIFs.</blockquote>",
                parse_mode=enums.ParseMode.HTML,
            )
            asyncio.create_task(_auto_del(s, 10))
            return
        s = await message.reply(
            list_gifs_text(gif_type),
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_del(s, 60))


async def _auto_del(msg, delay: int = 60):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass
