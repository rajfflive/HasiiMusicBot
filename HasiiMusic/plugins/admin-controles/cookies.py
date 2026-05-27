import os
import random
import time

import aiohttp
from pyrogram import filters, types

from HasiiMusic import app, config, logger, yt

_last_refresh_time: float = 0.0


@app.on_message(filters.command(["setcookies"]) & app.sudo_filter)
async def _set_cookies(_, m: types.Message):
    global _last_refresh_time
    try:
        await m.delete()
    except Exception:
        pass

    # Option 1: File reply
    if m.reply_to_message and m.reply_to_message.document:
        doc = m.reply_to_message.document
        if not doc.file_name or not doc.file_name.endswith(".txt"):
            return await m.reply_text(
                "<blockquote><b>❌ Galat File</b></blockquote>\n\n"
                "<blockquote>Sirf <b>.txt</b> file reply karo.</blockquote>"
            )
        sent = await m.reply_text("<blockquote><b>⏳ Saving...</b></blockquote>")
        try:
            path = f"HasiiMusic/cookies/cookie{random.randint(10000, 99999)}.txt"
            await m.reply_to_message.download(file_name=path)
            size = os.path.getsize(path)
            if size < 50:
                os.remove(path)
                return await sent.edit_text("<blockquote><b>❌ File empty/invalid</b></blockquote>")
            name = os.path.basename(path)
            if name not in yt.cookies:
                yt.cookies.append(name)
            yt.checked = True
            yt.warned = False
            yt.cookies_expired = False
            yt.last_cookie_alert = 0.0
            _last_refresh_time = time.time()
            await sent.edit_text(
                f"<blockquote><b>✅ Cookies Saved!</b></blockquote>\n\n"
                f"<blockquote>File: <code>{name}</code>\n"
                f"Size: <b>{size} bytes</b>\n"
                f"Total: <b>{len(yt.cookies)}</b> file(s)\n"
                f"Status: <b>✅ Active</b></blockquote>"
            )
        except Exception as e:
            await sent.edit_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")
        return

    # Option 2: URL
    if len(m.command) >= 2:
        url = m.command[1].strip()
        if not url.startswith("http"):
            return await m.reply_text(
                "<blockquote><b>❌ Invalid URL</b></blockquote>\n\n"
                "<blockquote>HTTP/HTTPS link do ya .txt file reply karo.</blockquote>"
            )
        sent = await m.reply_text("<blockquote><b>⏳ Downloading...</b></blockquote>")
        try:
            path = f"HasiiMusic/cookies/cookie{random.randint(10000, 99999)}.txt"
            link = url.replace("batbin.me/", "batbin.me/raw/") if "batbin.me" in url and "/raw/" not in url else url
            async with aiohttp.ClientSession() as session:
                async with session.get(link, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        return await sent.edit_text(
                            f"<blockquote><b>❌ HTTP {resp.status}</b>\nURL check karo.</blockquote>"
                        )
                    content = await resp.read()
                    if len(content) < 50:
                        return await sent.edit_text("<blockquote><b>❌ File empty/invalid</b></blockquote>")
                    with open(path, "wb") as f:
                        f.write(content)
            name = os.path.basename(path)
            if name not in yt.cookies:
                yt.cookies.append(name)
            yt.checked = True
            yt.warned = False
            yt.cookies_expired = False
            yt.last_cookie_alert = 0.0
            _last_refresh_time = time.time()
            await sent.edit_text(
                f"<blockquote><b>✅ Cookies Downloaded!</b></blockquote>\n\n"
                f"<blockquote>File: <code>{name}</code>\n"
                f"Size: <b>{len(content)} bytes</b>\n"
                f"Total: <b>{len(yt.cookies)}</b> file(s)\n"
                f"Status: <b>✅ Active</b></blockquote>"
            )
        except Exception as e:
            await sent.edit_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")
        return

    await m.reply_text(
        "<blockquote><b>📋 Usage</b></blockquote>\n\n"
        "<blockquote><b>URL se:</b>\n<code>/setcookies https://files.catbox.moe/abc.txt</code>\n\n"
        "<b>File se:</b>\ncookies.txt reply karke <code>/setcookies</code></blockquote>"
    )


@app.on_message(filters.command(["refreshcookies"]) & app.sudo_filter)
async def _refresh_cookies(_, m: types.Message):
    global _last_refresh_time
    try:
        await m.delete()
    except Exception:
        pass
    if not config.COOKIES_URL:
        return await m.reply_text(
            "<blockquote><b>❌ COOKIE_URL Set Nahi</b></blockquote>\n\n"
            "<blockquote>Pehle <code>/setcookies &lt;url&gt;</code> use karo.</blockquote>"
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
        yt.cookies_expired = False
        yt.last_cookie_alert = 0.0
        await yt.save_cookies(config.COOKIES_URL)
        _last_refresh_time = time.time()
        if yt.cookies:
            await sent.edit_text(
                f"<blockquote><b>✅ Cookies Refreshed!</b></blockquote>\n\n"
                f"<blockquote>Deleted: <b>{deleted}</b> old\n"
                f"Loaded: <b>{len(yt.cookies)}</b> new\n"
                f"Status: <b>✅ Active</b></blockquote>"
            )
        else:
            await sent.edit_text(
                "<blockquote><b>❌ Refresh Failed</b></blockquote>\n\n"
                "<blockquote>Cookies load nahi huin. URL check karo.</blockquote>"
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
            f"<blockquote><b>🗑️ Deleted</b></blockquote>\n\n"
            f"<blockquote><b>{deleted}</b> cookie file(s) removed.</blockquote>"
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

        if _last_refresh_time > 0:
            mins = int((now - _last_refresh_time) / 60)
            ago = f"{mins}m ago" if mins < 60 else f"{mins//60}h {mins%60}m ago"
            secs_left = (12 * 3600) - (now - _last_refresh_time)
            if secs_left > 0:
                nh, nm = int(secs_left // 3600), int((secs_left % 3600) // 60)
                next_str = f"in {nh}h {nm}m"
            else:
                next_str = "overdue"
        else:
            ago = "Never"
            next_str = "after first refresh"

        status = "❌ Expired" if yt.cookies_expired else ("✅ Active" if files else "⚠️ None")
        url_status = "✅ Set" if config.COOKIES_URL else "❌ Not set"

        file_list = ""
        for f in files:
            size = os.path.getsize(f"HasiiMusic/cookies/{f}")
            file_list += f"• <code>{f}</code> — {size} bytes\n"

        await m.reply_text(
            f"<blockquote><b>🍪 Cookie Status</b></blockquote>\n\n"
            f"<blockquote>"
            f"Status: <b>{status}</b>\n"
            f"Files: <b>{len(files)}</b>\n"
            f"COOKIE_URL: <b>{url_status}</b>\n"
            f"Last refresh: <b>{ago}</b>\n"
            f"Next auto-refresh: <b>{next_str}</b>\n\n"
            f"{file_list if file_list else '⚠️ No cookie files found'}"
            f"</blockquote>\n\n"
            f"<blockquote>"
            f"/refreshcookies — Abhi refresh karo\n"
            f"/setcookies &lt;url&gt; — Nayi cookies set karo\n"
            f"/delcookies — Saari delete karo"
            f"</blockquote>"
        )
    except Exception as e:
        await m.reply_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")
