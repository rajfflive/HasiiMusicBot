import os
import random
import time

import aiohttp
from pyrogram import filters, types

from HasiiMusic import app, config, logger, yt

_last_refresh_time: float = 0.0


@app.on_message(filters.command(["setcookies"]) & app.sudo_filter)
async def _set_cookies(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass

    if m.reply_to_message and m.reply_to_message.document:
        doc = m.reply_to_message.document
        if not doc.file_name or not doc.file_name.endswith(".txt"):
            return await m.reply_text(
                "<blockquote><b>❌ Galat File</b></blockquote>\n\n"
                "<blockquote>Sirf <b>.txt</b> cookies file reply karo.</blockquote>"
            )
        sent = await m.reply_text("<blockquote><b>⏳ Saving cookies...</b></blockquote>")
        try:
            path = f"HasiiMusic/cookies/cookie{random.randint(10000, 99999)}.txt"
            await m.reply_to_message.download(file_name=path)
            size = os.path.getsize(path)
            if size < 50:
                os.remove(path)
                return await sent.edit_text("<blockquote><b>❌ File too small/invalid</b></blockquote>")
            name = os.path.basename(path)
            if name not in yt.cookies:
                yt.cookies.append(name)
            yt.checked = True
            yt.warned = False
            global _last_refresh_time
            _last_refresh_time = time.time()
            await sent.edit_text(
                f"<blockquote><b>✅ Cookies Saved!</b></blockquote>\n\n"
                f"<blockquote>File: <code>{name}</code>\n"
                f"Size: <b>{size} bytes</b>\n"
                f"Total: <b>{len(yt.cookies)}</b> file(s)</blockquote>"
            )
        except Exception as e:
            await sent.edit_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")
        return

    if len(m.command) >= 2:
        url = m.command[1].strip()
        if not url.startswith("http"):
            return await m.reply_text(
                "<blockquote><b>❌ Invalid URL</b></blockquote>\n\n"
                "<blockquote>HTTP/HTTPS link do ya .txt file reply karo.</blockquote>"
            )
        sent = await m.reply_text("<blockquote><b>⏳ Downloading cookies...</b></blockquote>")
        try:
            path = f"HasiiMusic/cookies/cookie{random.randint(10000, 99999)}.txt"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        return await sent.edit_text(
                            f"<blockquote><b>❌ HTTP {resp.status}</b>\nURL check karo.</blockquote>"
                        )
                    content = await resp.read()
                    if len(content) < 50:
                        return await sent.edit_text(
                            "<blockquote><b>❌ File empty/invalid</b></blockquote>"
                        )
                    with open(path, "wb") as f:
                        f.write(content)
            name = os.path.basename(path)
            if name not in yt.cookies:
                yt.cookies.append(name)
            yt.checked = True
            yt.warned = False
            global _last_refresh_time
            _last_refresh_time = time.time()
            await sent.edit_text(
                f"<blockquote><b>✅ Cookies Downloaded!</b></blockquote>\n\n"
                f"<blockquote>File: <code>{name}</code>\n"
                f"Size: <b>{len(content)} bytes</b>\n"
                f"Total: <b>{len(yt.cookies)}</b> file(s)</blockquote>"
            )
        except Exception as e:
            await sent.edit_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")
        return

    await m.reply_text(
        "<blockquote><b>📋 Cookies Set Karne Ka Tarika</b></blockquote>\n\n"
        "<blockquote><b>Option 1 — URL se:</b>\n"
        "<code>/setcookies https://files.catbox.moe/abc.txt</code>\n\n"
        "<b>Option 2 — File se:</b>\n"
        "cookies.txt file ko reply karo aur <code>/setcookies</code> type karo</blockquote>"
    )


@app.on_message(filters.command(["refreshcookies"]) & app.sudo_filter)
async def _refresh_cookies(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass
    if not config.COOKIES_URL:
        return await m.reply_text(
            "<blockquote><b>❌ COOKIE_URL Set Nahi Hai</b></blockquote>\n\n"
            "<blockquote>Pehle <code>/setcookies &lt;url&gt;</code> se set karo.</blockquote>"
        )
    sent = await m.reply_text("<blockquote><b>⏳ Refreshing cookies...</b></blockquote>")
    try:
        deleted = 0
        for f in os.listdir("HasiiMusic/cookies"):
            if f.endswith(".txt") and f != "cookies.txt":
                os.remove(f"HasiiMusic/cookies/{f}")
                deleted += 1
        yt.cookies.clear()
        yt.checked = False
        yt.warned = False
        await yt.save_cookies(config.COOKIES_URL)
        global _last_refresh_time
        _last_refresh_time = time.time()
        if yt.cookies:
            await sent.edit_text(
                f"<blockquote><b>✅ Cookies Refreshed!</b></blockquote>\n\n"
                f"<blockquote>Deleted: <b>{deleted}</b> old file(s)\n"
                f"Loaded: <b>{len(yt.cookies)}</b> new file(s)</blockquote>"
            )
        else:
            await sent.edit_text(
                "<blockquote><b>❌ Refresh Failed</b></blockquote>\n\n"
                "<blockquote>Cookies download nahi huin. URL check karo.</blockquote>"
            )
    except Exception as e:
        await sent.edit_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")


@app.on_message(filters.command(["delcookies"]) & app.sudo_filter)
async def _del_cookies(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass
    deleted = 0
    try:
        for f in os.listdir("HasiiMusic/cookies"):
            if f.endswith(".txt") and f != "cookies.txt":
                os.remove(f"HasiiMusic/cookies/{f}")
                deleted += 1
        yt.cookies.clear()
        yt.checked = False
        yt.warned = False
        await m.reply_text(
            f"<blockquote><b>🗑️ Cookies Deleted</b></blockquote>\n\n"
            f"<blockquote><b>{deleted}</b> file(s) removed.</blockquote>"
        )
    except Exception as e:
        await m.reply_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")


@app.on_message(filters.command(["checkcookies"]) & app.sudo_filter)
async def _check_cookies(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass
    try:
        files = [f for f in os.listdir("HasiiMusic/cookies") if f.endswith(".txt")]
        now = time.time()
        refresh_ago = ""
        if _last_refresh_time > 0:
            mins = int((now - _last_refresh_time) / 60)
            if mins < 60:
                refresh_ago = f"{mins} min ago"
            else:
                refresh_ago = f"{mins // 60}h {mins % 60}m ago"
        else:
            refresh_ago = "Not refreshed yet"

        next_refresh_hrs = 12
        if _last_refresh_time > 0:
            next_secs = (next_refresh_hrs * 3600) - (now - _last_refresh_time)
            if next_secs > 0:
                next_h = int(next_secs // 3600)
                next_m = int((next_secs % 3600) // 60)
                next_str = f"in {next_h}h {next_m}m"
            else:
                next_str = "soon"
        else:
            next_str = "after first /refreshcookies"

        cookie_url_set = "✅ Set" if config.COOKIES_URL else "❌ Not set"

        if not files:
            return await m.reply_text(
                f"<blockquote><b>⚠️ No Cookies Found</b></blockquote>\n\n"
                f"<blockquote>COOKIE_URL: <b>{cookie_url_set}</b>\n"
                f"Use: <code>/setcookies &lt;url&gt;</code></blockquote>"
            )
        file_list = ""
        for f in files:
            size = os.path.getsize(f"HasiiMusic/cookies/{f}")
            file_list += f"• <code>{f}</code> — {size} bytes\n"
        await m.reply_text(
            f"<blockquote><b>🍪 Cookie Status</b></blockquote>\n\n"
            f"<blockquote>"
            f"Files: <b>{len(files)}</b>\n"
            f"COOKIE_URL: <b>{cookie_url_set}</b>\n"
            f"Last refresh: <b>{refresh_ago}</b>\n"
            f"Next auto-refresh: <b>{next_str}</b>\n\n"
            f"{file_list}"
            f"</blockquote>"
        )
    except Exception as e:
        await m.reply_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")
