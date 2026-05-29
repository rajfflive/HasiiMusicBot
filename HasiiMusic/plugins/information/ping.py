"""
Ping Plugin — v2 with GIF Manager
/ping or /alive → sends GIF (from DB) + stats

GIF Management (owner/sudo only):
  /setpinggif       - Reply to GIF → add to ping list
  /setpinggif naam  - Reply to GIF + custom name
  /rmpinggif <n>    - Remove ping GIF by number
  /listpinggif      - See all ping GIFs with numbers
"""

import time
import psutil

from pyrogram import filters, types

from HasiiMusic import app, tune, boot, config, lang
from HasiiMusic.helpers import buttons
from HasiiMusic.helpers.gif_manager import get_random_gif, register_gif_commands

# ─── Register GIF management commands ────────────────────────────────────────
register_gif_commands(app, "ping", "ping")


@app.on_message(filters.command(["alive", "ping"]) & ~app.bl_users)
@lang.language()
async def _ping(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass

    start = time.time()
    sent = await m.reply_text(m.lang["pinging"])

    def get_time(s):
        return (lambda r: (f"{r[-1]}, " if r[-1][:-4] != "0" else "") + ":".join(reversed(r[:-1])))(
            [f"{v}{u}" for v, u in zip([s % 60, (s // 60) % 60, (s // 3600) % 24, s // 86400], ["s", "m", "h", "days"])])

    uptime = get_time(int(time.time() - boot))
    latency = round((time.time() - start) * 1000, 2)

    mem = psutil.virtual_memory()
    ram_usage = f"{round(mem.used / (1024 ** 3), 1)}GB / {round(mem.total / (1024 ** 3), 1)}GB"
    cpu_percent = psutil.cpu_percent(interval=0.5)

    from HasiiMusic import db
    active_chats = len(await db.get_chats())

    caption_text = m.lang["ping_pong"].format(
        latency, uptime, await tune.ping(), ram_usage, cpu_percent, active_chats,
    )

    ping_gif = get_random_gif("ping")

    if ping_gif:
        try:
            await sent.delete()
            await m.reply_animation(
                animation=ping_gif,
                caption=caption_text,
                reply_markup=buttons.ping_markup(m.lang["support"]),
            )
            return
        except Exception:
            pass

    try:
        await sent.edit_media(
            media=types.InputMediaPhoto(
                media=config.PING_IMG,
                caption=caption_text
            ),
            reply_markup=buttons.ping_markup(m.lang["support"]),
        )
    except Exception:
        await sent.edit_text(
            text=caption_text,
            reply_markup=buttons.ping_markup(m.lang["support"]),
        )
