import os
import random
import time
import aiohttp
from pyrogram import filters, types
from HasiiMusic import app, config, yt

_last_refresh_time: float = 0.0


def _cookie_dir_files():
    try:
        os.makedirs("HasiiMusic/cookies", exist_ok=True)
        return [f for f in os.listdir("HasiiMusic/cookies") if f.endswith(".txt")]
    except Exception:
        return []


@app.on_message(filters.command(["setcookies"]) & app.sudo_filter)
async def _set_cookies(_, m: types.Message):
    global _last_refresh_time
    try:
        await m.delete()
    except Exception:
        pass

    if m.reply_to_message and m.reply_to_message.document:
        doc = m.reply_to_message.document
        if not doc.file_name or not doc.file_name.endswith(".txt"):
            return await m.reply_text("<blockquote><b>❌ Sirf .txt file reply karo.</b></blockquote>")
        sent = await m.reply_text("<blockquote><b>⏳ Saving...</b></blockquote>")
        try:
            os.makedirs("HasiiMusic/cookies", exist_ok=True)
            path = f"HasiiMusic/cookies/cookie{random.randint(10000,99999)}.txt"
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
            return await sent.edit_text(
                f"<blockquote><b>✅ Saved!</b></blockquote>\n\n"
                f"<blockquote>File: <code>{name}</code>\n"
                f"Size: <b>{size} bytes</b>\n"
                f"Total: <b>{len(yt.cookies)}</b></blockquote>"
            )
        except Exception as e:
            return await sent.edit_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")

    if len(m.command) >= 2:
        url = m.command[1].strip()
        if not url.startswith("http"):
            return await m.reply_text("<blockquote><b>❌ Valid HTTP URL do.</b></blockquote>")
        sent = await m.reply_text("<blockquote><b>⏳ Downloading...</b></blockquote>")
        try:
            os.makedirs("HasiiMusic/cookies", exist_ok=True)
            path = f"HasiiMusic/cookies/cookie{random.randint(10000,99999)}.txt"
            link = url.replace("batbin.me/", "batbin.me/raw/") \
                if ("batbin.me" in url and "/raw/" not in url) else url
            async with aiohttp.ClientSession() as session:
                async with session.get(link, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        return await sent.edit_text(f"<blockquote><b>❌ HTTP {resp.status}</b></blockquote>")
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
            return await sent.edit_text(
                f"<blockquote><b>✅ Downloaded!</b></blockquote>\n\n"
                f"<blockquote>File: <code>{name}</code>\n"
                f"Size: <b>{len(content)} bytes</b>\n"
                f"Total: <b>{len(yt.cookies)}</b></blockquote>"
            )
        except Exception as e:
            return await sent.edit_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")

    await m.reply_text(
        "<blockquote><b>📋 Usage</b></blockquote>\n\n"
        "<blockquote><b>URL se:</b>\n<code>/setcookies https://files.catbox.moe/abc.txt</code>\n\n"
        "<b>File se:</b>\ncookies.txt reply karo phir <code>/setcookies</code></blockquote>"
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
            "<blockquote><b>❌ COOKIE_URL set nahi.\nPehle /setcookies use karo.</b></blockquote>"
        )
    sent = await m.reply_text("<blockquote><b>⏳ Refreshing...</b></blockquote>")
    try:
        deleted = 0
        os.makedirs("HasiiMusic/cookies", exist_ok=True)
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
                f"<blockquote><b>✅ Refreshed!</b></blockquote>\n\n"
                f"<blockquote>Deleted: <b>{deleted}</b>\nLoaded: <b>{len(yt.cookies)}</b></blockquote>"
            )
        else:
            await sent.edit_text(
                "<blockquote><b>❌ Failed — Invidious fallback active.</b></blockquote>"
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
        os.makedirs("HasiiMusic/cookies", exist_ok=True)
        for f in os.listdir("HasiiMusic/cookies"):
            if f.endswith(".txt") and f != "cookies.txt":
                os.remove(f"HasiiMusic/cookies/{f}")
                deleted += 1
        yt.cookies.clear()
        yt.checked = False
        yt.warned = False
        await m.reply_text(
            f"<blockquote><b>🗑️ {deleted} file(s) deleted.\n"
            f"Invidious fallback active.</b></blockquote>"
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
        files = _cookie_dir_files()
        now = time.time()

        if _last_refresh_time > 0:
            mins = int((now - _last_refresh_time) / 60)
            ago = f"{mins}m ago" if mins < 60 else f"{mins//60}h {mins%60}m ago"
            sl = (12 * 3600) - (now - _last_refresh_time)
            next_str = f"in {int(sl//3600)}h {int((sl%3600)//60)}m" if sl > 0 else "⚠️ Overdue"
        else:
            ago = "Never"
            next_str = "after first /refreshcookies"

        status = "❌ Expired" if yt.cookies_expired else ("✅ Active" if files else "⚠️ None")
        inv_status = "✅ Active" if (not files or yt.cookies_expired) else "⏸ Standby"
        url_set = "✅ Set" if config.COOKIES_URL else "❌ Not set"

        file_list = ""
        for f in files:
            try:
                size = os.path.getsize(f"HasiiMusic/cookies/{f}")
                file_list += f"• <code>{f}</code> — {size} bytes\n"
            except Exception:
                file_list += f"• <code>{f}</code>\n"

        if not file_list:
            file_list = "⚠️ No cookie files found\n"

        await m.reply_text(
            f"<blockquote><b>🍪 Cookie Status</b></blockquote>\n\n"
            f"<blockquote>"
            f"Status: <b>{status}</b>\n"
            f"Files: <b>{len(files)}</b>\n"
            f"COOKIE_URL: <b>{url_set}</b>\n"
            f"Last refresh: <b>{ago}</b>\n"
            f"Next auto: <b>{next_str}</b>\n"
            f"Invidious: <b>{inv_status}</b>\n\n"
            f"{file_list}"
            f"</blockquote>\n"
            f"<blockquote>"
            f"/refreshcookies — Abhi refresh karo\n"
            f"/setcookies &lt;url&gt; — Nayi cookies\n"
            f"/delcookies — Saari delete karo\n"
            f"/testplay — YouTube test karo"
            f"</blockquote>"
        )
    except Exception as e:
        await m.reply_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")


@app.on_message(filters.command(["testplay"]) & app.sudo_filter)
async def _test_play(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass
    sent = await m.reply_text("<blockquote><b>⏳ Testing YouTube...</b></blockquote>")
    try:
        import time as t
        start = t.time()
        result = await yt.download("dQw4w9WgXcQ", is_live=False, video=False)
        elapsed = round(t.time() - start, 1)
        if result:
            method = "🌐 Invidious (URL)" if result.startswith("http") else "📥 yt-dlp (File)"
            cookies_used = len(yt.cookies)
            await sent.edit_text(
                f"<blockquote><b>✅ Test Passed!</b></blockquote>\n\n"
                f"<blockquote>Method: <b>{method}</b>\n"
                f"Time: <b>{elapsed}s</b>\n"
                f"Cookies: <b>{cookies_used} file(s)</b>\n"
                f"Status: <b>Working ✅</b></blockquote>"
            )
        else:
            await sent.edit_text(
                f"<blockquote><b>❌ Test Failed!</b></blockquote>\n\n"
                f"<blockquote>Sab methods fail ho gaye.\n"
                f"Time: <b>{elapsed}s</b></blockquote>"
            )
    except Exception as e:
        await sent.edit_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")
