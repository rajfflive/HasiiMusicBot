# ==============================================================================
# cookies.py - YouTube Cookies Manager (Sudo Only)
# ==============================================================================
# Commands:
# - /setcookies <url>  — URL se cookies download karo
# - /setcookies        — Reply mein .txt file bhejo cookies set karne ke liye
# - /delcookies        — Saari cookies delete karo
# - /checkcookies      — Cookie files ka status dekho
# ==============================================================================

import os
import random

import aiohttp
from pyrogram import filters, types

from HasiiMusic import app, logger, yt


@app.on_message(filters.command(["setcookies"]) & app.sudo_filter)
async def _set_cookies(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass

    # --- Option 1: File reply kiya hai ---
    if m.reply_to_message and m.reply_to_message.document:
        doc = m.reply_to_message.document
        if not doc.file_name or not doc.file_name.endswith(".txt"):
            return await m.reply_text(
                "<blockquote><b>❌ Galat File</b></blockquote>\n\n"
                "<blockquote>Sirf <b>.txt</b> cookies file reply karo.</blockquote>"
            )
        sent = await m.reply_text(
            "<blockquote><b>⏳ Cookies save ho rahi hain...</b></blockquote>"
        )
        try:
            path = f"HasiiMusic/cookies/cookie{random.randint(10000, 99999)}.txt"
            await m.reply_to_message.download(file_name=path)
            size = os.path.getsize(path)
            if size < 50:
                os.remove(path)
                return await sent.edit_text(
                    "<blockquote><b>❌ File Khaali Hai</b></blockquote>\n\n"
                    "<blockquote>Cookies file valid nahi hai.</blockquote>"
                )
            cookie_filename = os.path.basename(path)
            if cookie_filename not in yt.cookies:
                yt.cookies.append(cookie_filename)
            yt.checked = True
            yt.warned = False
            await sent.edit_text(
                f"<blockquote><b>✅ Cookies Save Ho Gayi!</b></blockquote>\n\n"
                f"<blockquote>File: <code>{cookie_filename}</code>\n"
                f"Size: <b>{size} bytes</b>\n"
                f"Total cookies: <b>{len(yt.cookies)}</b></blockquote>"
            )
        except Exception as e:
            await sent.edit_text(
                f"<blockquote><b>❌ Error</b></blockquote>\n\n"
                f"<blockquote>{str(e)}</blockquote>"
            )
        return

    # --- Option 2: URL diya hai ---
    if len(m.command) >= 2:
        url = m.command[1].strip()
        if not url.startswith("http"):
            return await m.reply_text(
                "<blockquote><b>❌ Invalid URL</b></blockquote>\n\n"
                "<blockquote>HTTP/HTTPS link do ya .txt file reply karo.</blockquote>"
            )
        sent = await m.reply_text(
            "<blockquote><b>⏳ URL se cookies download ho rahi hain...</b></blockquote>"
        )
        try:
            path = f"HasiiMusic/cookies/cookie{random.randint(10000, 99999)}.txt"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        return await sent.edit_text(
                            f"<blockquote><b>❌ Download Failed</b></blockquote>\n\n"
                            f"<blockquote>HTTP Error: <b>{resp.status}</b>\n"
                            f"URL check karo.</blockquote>"
                        )
                    content = await resp.read()
                    if len(content) < 50:
                        return await sent.edit_text(
                            "<blockquote><b>❌ File Khaali Hai</b></blockquote>\n\n"
                            "<blockquote>URL se khaali ya invalid file aayi.</blockquote>"
                        )
                    with open(path, "wb") as f:
                        f.write(content)

            cookie_filename = os.path.basename(path)
            if cookie_filename not in yt.cookies:
                yt.cookies.append(cookie_filename)
            yt.checked = True
            yt.warned = False
            await sent.edit_text(
                f"<blockquote><b>✅ Cookies Download Ho Gayi!</b></blockquote>\n\n"
                f"<blockquote>File: <code>{cookie_filename}</code>\n"
                f"Size: <b>{len(content)} bytes</b>\n"
                f"Total cookies: <b>{len(yt.cookies)}</b></blockquote>"
            )
        except Exception as e:
            await sent.edit_text(
                f"<blockquote><b>❌ Error</b></blockquote>\n\n"
                f"<blockquote>{str(e)}</blockquote>"
            )
        return

    # --- Kuch nahi diya ---
    await m.reply_text(
        "<blockquote><b>📋 Cookies Set Karne Ka Tarika</b></blockquote>\n\n"
        "<blockquote><b>Option 1 — URL se:</b>\n"
        "<code>/setcookies https://files.catbox.moe/abc.txt</code>\n\n"
        "<b>Option 2 — File se:</b>\n"
        "cookies.txt file reply karo aur <code>/setcookies</code> likho</blockquote>"
    )


@app.on_message(filters.command(["delcookies"]) & app.sudo_filter)
async def _del_cookies(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass

    cookies_dir = "HasiiMusic/cookies"
    deleted = 0
    try:
        for file in os.listdir(cookies_dir):
            if file.endswith(".txt") and file != "cookies.txt":
                os.remove(os.path.join(cookies_dir, file))
                deleted += 1
        yt.cookies.clear()
        yt.checked = False
        yt.warned = False
        await m.reply_text(
            f"<blockquote><b>🗑️ Cookies Delete Ho Gayi</b></blockquote>\n\n"
            f"<blockquote><b>{deleted}</b> cookie file(s) delete ki gayi.</blockquote>"
        )
    except Exception as e:
        await m.reply_text(
            f"<blockquote><b>❌ Error</b></blockquote>\n\n"
            f"<blockquote>{str(e)}</blockquote>"
        )


@app.on_message(filters.command(["checkcookies"]) & app.sudo_filter)
async def _check_cookies(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass

    cookies_dir = "HasiiMusic/cookies"
    try:
        files = [f for f in os.listdir(cookies_dir) if f.endswith(".txt")]
        if not files:
            return await m.reply_text(
                "<blockquote><b>⚠️ Koi Cookies Nahi Hain</b></blockquote>\n\n"
                "<blockquote>Use karo: <code>/setcookies &lt;url&gt;</code></blockquote>"
            )
        file_list = ""
        for f in files:
            size = os.path.getsize(os.path.join(cookies_dir, f))
            file_list += f"• <code>{f}</code> — {size} bytes\n"
        await m.reply_text(
            f"<blockquote><b>🍪 Cookie Files ({len(files)})</b></blockquote>\n\n"
            f"<blockquote>{file_list}</blockquote>"
        )
    except Exception as e:
        await m.reply_text(
            f"<blockquote><b>❌ Error</b></blockquote>\n\n"
            f"<blockquote>{str(e)}</blockquote>"
        )
