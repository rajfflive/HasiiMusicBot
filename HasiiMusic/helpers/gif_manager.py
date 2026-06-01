"""
GIF Manager — Full Version
Place at: HasiiMusic/helpers/gif_manager.py
"""

import random
from pyrogram import enums, filters

# ── GIF Library ───────────────────────────────────────────────────────────────

_GIFS: dict[str, list[str]] = {

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
        "https://media.tenor.com/0CzJAIVR8DAAAAAC/anime-welcome.gif",
        "https://media.tenor.com/uFzNvBn8BYYAAAAC/waving-hi.gif",
    ],

    "goodbye": [
        "https://media.tenor.com/X_3Jp0TlgsYAAAAC/bye-anime.gif",
        "https://media.tenor.com/4dIPYW0Y3XAAAAAC/goodbye-anime.gif",
        "https://media.tenor.com/H_H3RNPB5KEAAAAC/bye-bye-anime.gif",
        "https://media.tenor.com/dghQO8s6GakAAAAC/anime-goodbye.gif",
        "https://media.tenor.com/k4GF5H_mhFMAAAAC/wave-goodbye-anime.gif",
    ],

    "couple": [
        "https://media.tenor.com/B-iaTsFenUoAAAAC/anime-couple.gif",
        "https://media.tenor.com/Ld-cDzuBuKMAAAAC/anime-love.gif",
        "https://media.tenor.com/8U0_pIrTbPoAAAAC/anime-couple-love.gif",
        "https://media.tenor.com/JaR0lVvHmDIAAAAC/cute-couple-anime.gif",
        "https://media.tenor.com/T9b5qsMHWrUAAAAC/love-anime.gif",
        "https://media.tenor.com/OmBcFUMlKAEAAAAC/anime-kiss.gif",
        "https://media.tenor.com/uIkUi_khlbkAAAAC/anime-hug.gif",
        "https://media.tenor.com/nTLkYZaafTAAAAAC/couple-hug.gif",
    ],

    "tagall": [
        "https://media.tenor.com/fY8iU9gBSsIAAAAC/anime-attention.gif",
        "https://media.tenor.com/5hGlkFj6MBoAAAAC/notification-alert.gif",
        "https://media.tenor.com/9j1FaTHCKJwAAAAC/anime-announcement.gif",
        "https://media.tenor.com/kG2aSAJhipgAAAAC/anime-calling.gif",
        "https://media.tenor.com/ZlVBZOcnFqIAAAAC/attention-anime.gif",
        "https://media.tenor.com/4tNpbdALFN0AAAAC/everyone-listen.gif",
    ],

    "tagadmins": [
        "https://media.tenor.com/Qlg5KUHLf5UAAAAC/anime-serious.gif",
        "https://media.tenor.com/QGbJTSiGjBYAAAAC/anime-alert.gif",
        "https://media.tenor.com/eXSk3VVDGKUAAAAC/anime-police.gif",
        "https://media.tenor.com/hJkfCnexdE4AAAAC/serious-face.gif",
    ],

    "roasttag": [
        "https://media.tenor.com/PmV8wJbdZOkAAAAC/anime-fire.gif",
        "https://media.tenor.com/HNmSIuFMHEAAAAAC/anime-roast.gif",
        "https://media.tenor.com/lz_-mjPLEpYAAAAC/anime-burn.gif",
        "https://media.tenor.com/jk2h5lnJVPkAAAAC/fire-anime.gif",
        "https://media.tenor.com/3Lj1vQU8YuYAAAAC/roasting-meme.gif",
    ],

    "gmtag": [
        "https://media.tenor.com/tUv8V9cHFRoAAAAC/good-morning-anime.gif",
        "https://media.tenor.com/N3HZYC0hG5YAAAAC/anime-good-morning.gif",
        "https://media.tenor.com/uRKRzGV_KsAAAAC/morning-coffee.gif",
        "https://media.tenor.com/LLRxXpfnVuUAAAAC/anime-sunrise.gif",
        "https://media.tenor.com/qST5QXNLPOMAAAAC/good-morning.gif",
        "https://media.tenor.com/vI0YFb-cxoIAAAAC/anime-morning.gif",
    ],

    "gntag": [
        "https://media.tenor.com/4tBzFqjPBikAAAAC/good-night-anime.gif",
        "https://media.tenor.com/k1f7iBMCo6IAAAAC/anime-good-night.gif",
        "https://media.tenor.com/AUNhkFJ7N-cAAAAC/night-sleep.gif",
        "https://media.tenor.com/0TDEbsXlwfkAAAAC/anime-sleep-night.gif",
        "https://media.tenor.com/mJvuyq5Z0AQAAAAC/good-night.gif",
        "https://media.tenor.com/VqGixHUYVWcAAAAC/anime-night.gif",
    ],

    "gdtag": [
        "https://media.tenor.com/CWaBheLuqf4AAAAC/good-afternoon-anime.gif",
        "https://media.tenor.com/FZrGCQvFCy0AAAAC/afternoon-anime.gif",
        "https://media.tenor.com/uDN7XFCUQ7AAAAAC/good-afternoon.gif",
        "https://media.tenor.com/Nz1OlGjnmQEAAAAC/anime-afternoon.gif",
    ],

    "gevtag": [
        "https://media.tenor.com/vRiPTl2GLHMAAAAC/good-evening-anime.gif",
        "https://media.tenor.com/q0Z0T2O3DAAAAAAC/evening-anime.gif",
        "https://media.tenor.com/lh0wuwEuehMAAAAC/good-evening.gif",
        "https://media.tenor.com/mHb4aF8H-ZYAAAAC/anime-evening.gif",
    ],

    "gbdtag": [
        "https://media.tenor.com/gJB41QnTGm8AAAAC/anime-birthday.gif",
        "https://media.tenor.com/Bv_uMzWA-scAAAAC/happy-birthday-anime.gif",
        "https://media.tenor.com/iF0s2xA0_MoAAAAC/birthday-cake.gif",
        "https://media.tenor.com/wnV6s7bVA7QAAAAC/birthday-anime.gif",
        "https://media.tenor.com/PFlS1Hxf5HEAAAAC/happy-bday.gif",
    ],
}

# Custom GIFs set by admins
_custom_gifs: dict[str, list[str]] = {}


# ── Core Functions ────────────────────────────────────────────────────────────

def get_random_gif(gif_type: str) -> str | None:
    """Return a random GIF URL for the given type, or None if unavailable."""
    custom = _custom_gifs.get(gif_type, [])
    default = _GIFS.get(gif_type, [])
    pool = custom if custom else default
    return random.choice(pool) if pool else None


def add_custom_gif(gif_type: str, url: str):
    """Add a custom GIF URL for a type."""
    if gif_type not in _custom_gifs:
        _custom_gifs[gif_type] = []
    if url not in _custom_gifs[gif_type]:
        _custom_gifs[gif_type].append(url)


def reset_custom_gifs(gif_type: str):
    """Remove all custom GIFs for a type (revert to defaults)."""
    _custom_gifs.pop(gif_type, None)


def list_gif_types() -> list[str]:
    """List all available GIF types."""
    return sorted(_GIFS.keys())


# ── Auth Helper ───────────────────────────────────────────────────────────────

async def is_owner_or_sudo(user_id: int) -> bool:
    """Check if a user is the bot owner or has sudo privileges."""
    try:
        from HasiiMusic import OWNER_ID
        if isinstance(OWNER_ID, (list, tuple)):
            owners = [int(x) for x in OWNER_ID]
        else:
            owners = [int(OWNER_ID)]
        if user_id in owners:
            return True
    except Exception:
        pass

    try:
        from HasiiMusic import SUDO_USERS
        if SUDO_USERS:
            if isinstance(SUDO_USERS, (list, tuple, set)):
                sudos = [int(x) for x in SUDO_USERS]
            else:
                sudos = [int(SUDO_USERS)]
            if user_id in sudos:
                return True
    except Exception:
        pass

    return False


# ── Register GIF Commands ─────────────────────────────────────────────────────

def register_gif_commands(app, gif_type: str, prefix: str):
    """
    Registers admin commands to set/reset GIFs for a type.
    /setgif<prefix> <url>  — add custom gif
    /resetgif<prefix>      — reset to default
    """
    import asyncio

    set_cmd = f"setgif{prefix}"
    reset_cmd = f"resetgif{prefix}"

    @app.on_message(filters.command(set_cmd) & filters.group)
    async def _set_gif(_, message):
        try:
            member = await app.get_chat_member(message.chat.id, message.from_user.id)
            if member.status not in (
                enums.ChatMemberStatus.ADMINISTRATOR,
                enums.ChatMemberStatus.OWNER,
            ):
                return
        except Exception:
            return

        args = message.command[1:]
        if not args:
            await message.reply(
                f"<blockquote>⚠️ Usage: /{set_cmd} &lt;gif_url&gt;</blockquote>",
                parse_mode=enums.ParseMode.HTML,
            )
            return

        add_custom_gif(gif_type, args[0].strip())
        sent = await message.reply(
            f"<blockquote>✅ Custom GIF added for <b>{gif_type}</b>!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_del(sent, 15))

    @app.on_message(filters.command(reset_cmd) & filters.group)
    async def _reset_gif(_, message):
        try:
            member = await app.get_chat_member(message.chat.id, message.from_user.id)
            if member.status not in (
                enums.ChatMemberStatus.ADMINISTRATOR,
                enums.ChatMemberStatus.OWNER,
            ):
                return
        except Exception:
            return

        reset_custom_gifs(gif_type)
        sent = await message.reply(
            f"<blockquote>♻️ GIFs reset to default for <b>{gif_type}</b>.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(_auto_del(sent, 15))


async def _auto_del(msg, delay: int = 60):
    import asyncio
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass
