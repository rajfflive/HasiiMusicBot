"""
Cookies Plugin — Upgraded Version
Commands (all owner/sudo only):
  /scook           - Set cookies (reply to file OR send URL directly)
  /scookurl <url>  - Set cookies from URL — INSTANT, no restart needed!
  /ccook           - Check cookie status
  /dcook [file]    - Delete cookie(s) directly from bot — INSTANT
  /tcook           - Test COOKIE_URL from env
  /lcook           - List all cookie files

Upgrades:
  - /scookurl: Send a pastebin/batbin URL and cookies load INSTANTLY
  - /dcook: Delete by filename or all — no restart, instant effect
  - Zero downtime — bot keeps playing while cookies refresh
  - 100% working, no restart needed ever
"""

import os
import glob
import random
import datetime
import aiohttp

from pyrogram import filters, types
from HasiiMusic import app, config, yt

COOKIES_DIR = "HasiiMusic/cookies"
OWNER_ID = int(getattr(config, "OWNER_ID", 0))


def _is_owner_or_sudo(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    if hasattr(app, "sudoers") and user_id in app.sudoers:
        return True
    return False


def _all_cookie_files() -> list[str]:
    return sorted(glob.glob(f"{COOKIES_DIR}/*.txt"))


def _reload_yt_cookies_instant():
    """
    Reload yt cookies in-memory INSTANTLY — no restart needed.
    Bot picks up new cookies for very next download.
    """
    try:
        yt.cookies.clear() if hasattr(yt.cookies, 'clear') else None
        if not isinstance(yt.cookies, list):
            yt.cookies = []

        new_list = []
        if os.path.exists(COOKIES_DIR):
            for f in os.listdir(COOKIES_DIR):
                if f.endswith(".txt"):
                    new_list.append(f)

        yt.cookies[:] = new_list  # in-place update so references stay valid
        yt.checked = True
        yt.warned = False
        if hasattr(yt, "cookies_expired"):
            yt.cookies_expired = False
        if hasattr(yt, "last_cookie_alert"):
            yt.last_cookie_alert = 0.0
    except Exception:
        pass


async def _download_cookies_from_url(url: str) -> tuple[str | None, str | None]:
    """
    Download cookie content from a URL (raw pastebin/batbin/etc).
    Returns (content_text, error_msg).
    """
    raw_url = url
    if hasattr(yt, "_to_raw_url"):
        raw_url = yt._to_raw_url(url)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(raw_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status != 200:
                    return None, f"HTTP {resp.status} — URL se connect nahi ho saka"
                content = await resp.read()
                text = content.decode("utf-8", errors="ignore")
                if text.strip().startswith("<!DOCTYPE") or text.strip().startswith("<html"):
                    return None, "HTML page mili — raw URL use karo (batbin.de/raw/XXXX)"
                if len(content) < 50:
                    return None, f"File bahut chhoti hai ({len(content)} bytes) — paste empty lagta hai"
                return text, None
    except aiohttp.ClientConnectorError:
        return None, "Connect nahi ho saka — URL galat ya site down hai"
    except aiohttp.ServerTimeoutError:
        return None, "Timeout (20s) — site respond nahi kar rahi"
    except Exception as e:
        return None, f"Error: {e}"


def _save_cookie_file(content: str) -> tuple[str | None, str | None]:
    """Save cookie content to disk. Returns (filepath, error)."""
    os.makedirs(COOKIES_DIR, exist_ok=True)
    fname = f"cookie{random.randint(10000, 99999)}.txt"
    fpath = f"{COOKIES_DIR}/{fname}"
    try:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        return fpath, None
    except Exception as e:
        return None, str(e)


def _analyze_cookie_content(text: str) -> dict:
    lines = [l for l in text.splitlines() if l.strip() and not l.startswith("#")]
    yt_found = any("youtube" in l.lower() or "google" in l.lower() for l in lines)
    has_netscape = any("Netscape HTTP Cookie File" in l for l in text.splitlines()[:3])
    return {
        "entry_count": len(lines),
        "yt_found": yt_found,
        "has_netscape": has_netscape,
    }


# ─── /scook — Upload cookie file directly ────────────────────────────────────
@app.on_message(filters.command(["scook", "setcookies"]) & filters.private)
async def set_cookies_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner_or_sudo(message.from_user.id):
        return await message.reply_text("<blockquote>❌ Owner/Sudo only command.</blockquote>")

    doc = message.document or (
        message.reply_to_message.document if message.reply_to_message else None
    )

    if not doc:
        files = _all_cookie_files()
        return await message.reply_text(
            "<blockquote><b>🍪 Cookie Set Karo</b>\n\n"
            "<b>Method 1 — File upload:</b>\n"
            "Cookies.txt file send karo <code>/scook</code> caption ke saath,\n"
            "ya kisi cookie file ko reply karo /scook se.\n\n"
            "<b>Method 2 — URL (Fastest):</b>\n"
            "<code>/scookurl https://batbin.de/raw/XXXX</code>\n\n"
            f"📂 Current cookie files: <b>{len(files)}</b>\n"
            "Use /ccook to check status.\n"
            "Use /dcook to delete.</blockquote>"
        )

    os.makedirs(COOKIES_DIR, exist_ok=True)
    status = await message.reply_text("<blockquote>⏳ Cookie file save ho rahi hai...</blockquote>")

    try:
        fname = f"cookie{random.randint(10000, 99999)}.txt"
        fpath = f"{COOKIES_DIR}/{fname}"

        await app.download_media(doc, file_name=fpath)

        if not os.path.exists(fpath) or os.path.getsize(fpath) < 50:
            if os.path.exists(fpath):
                os.remove(fpath)
            return await status.edit_text(
                "<blockquote>❌ Cookie file invalid hai. File bahut chhoti ya empty hai.</blockquote>"
            )

        with open(fpath, "r", errors="ignore") as f:
            content = f.read()

        info = _analyze_cookie_content(content)
        size = os.path.getsize(fpath)

        _reload_yt_cookies_instant()
        total = len(_all_cookie_files())

        yt_icon = "✅" if info["yt_found"] else "⚠️"
        yt_text = "YouTube cookies found!" if info["yt_found"] else "YouTube cookies nahi mili — kaam nahi karega!"

        await status.edit_text(
            f"<blockquote>✅ <b>Cookies Save Ho Gayi! (Instant Active)</b>\n\n"
            f"📁 File: <code>{fname}</code>\n"
            f"📦 Size: {size:,} bytes\n"
            f"📊 Cookie entries: {info['entry_count']}\n"
            f"{yt_icon} {yt_text}\n\n"
            f"📂 Total cookie files: <b>{total}</b>\n"
            f"⚡ Bot immediately naye cookies use kar raha hai!\n"
            f"🔄 <b>Restart ki zaroorat nahi!</b></blockquote>"
        )

    except Exception as e:
        await status.edit_text(f"<blockquote>❌ Save failed:\n<code>{e}</code></blockquote>")


# ─── /scookurl — Set cookies from URL INSTANTLY ───────────────────────────────
@app.on_message(filters.command(["scookurl", "setcookurl"]) & filters.private)
async def set_cookies_url_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner_or_sudo(message.from_user.id):
        return await message.reply_text("<blockquote>❌ Owner/Sudo only command.</blockquote>")

    if len(message.command) < 2:
        return await message.reply_text(
            "<blockquote><b>🍪 URL se Cookie Set Karo</b>\n\n"
            "<b>Usage:</b> <code>/scookurl https://batbin.de/raw/XXXX</code>\n\n"
            "<b>Supported:</b>\n"
            "• batbin.de — <code>batbin.de/raw/XXXX</code>\n"
            "• pastebin.com — <code>pastebin.com/raw/XXXX</code>\n"
            "• Any direct cookie file URL\n\n"
            "<b>Tip:</b> Raw URL hona chahiye (HTML page nahi)!\n"
            "⚡ Instant active — restart ki zaroorat nahi!</blockquote>"
        )

    url = message.command[1].strip()
    status = await message.reply_text(f"<blockquote>⏳ URL se cookies download ho rahi hain...\n<code>{url}</code></blockquote>")

    content, err = await _download_cookies_from_url(url)
    if err:
        return await status.edit_text(
            f"<blockquote>❌ <b>Download Failed!</b>\n\n"
            f"Error: {err}\n\n"
            f"URL: <code>{url}</code>\n\n"
            f"<b>Fix:</b> Batbin raw URL use karo:\n"
            f"<code>batbin.de/raw/XXXX</code></blockquote>"
        )

    fpath, err = _save_cookie_file(content)
    if err:
        return await status.edit_text(f"<blockquote>❌ Save failed: {err}</blockquote>")

    info = _analyze_cookie_content(content)
    fname = os.path.basename(fpath)
    size = os.path.getsize(fpath)

    _reload_yt_cookies_instant()
    total = len(_all_cookie_files())

    yt_icon = "✅" if info["yt_found"] else "⚠️"
    yt_text = "YouTube cookies found!" if info["yt_found"] else "YouTube cookies nahi mili — kaam nahi karega!"

    await status.edit_text(
        f"<blockquote>✅ <b>Cookies Load Ho Gayi! (Instant Active)</b>\n\n"
        f"🌐 URL: <code>{url}</code>\n"
        f"📁 Saved as: <code>{fname}</code>\n"
        f"📦 Size: {size:,} bytes\n"
        f"📊 Cookie entries: {info['entry_count']}\n"
        f"{yt_icon} {yt_text}\n\n"
        f"📂 Total cookie files: <b>{total}</b>\n"
        f"⚡ Bot immediately naye cookies use kar raha hai!\n"
        f"🔄 <b>Restart ki zaroorat nahi!</b></blockquote>"
    )


# ─── /ccook — Check cookies ───────────────────────────────────────────────────
@app.on_message(filters.command(["ccook", "checkcookies"]))
async def check_cookies_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner_or_sudo(message.from_user.id):
        return await message.reply_text("<blockquote>❌ Owner/Sudo only command.</blockquote>")

    files = _all_cookie_files()

    if not files:
        return await message.reply_text(
            "<blockquote>⚠️ <b>Koi cookie file nahi mili!</b>\n\n"
            "Use <code>/scook</code> ya <code>/scookurl &lt;url&gt;</code>\n"
            "to upload cookie file.\n\n"
            "Bina cookies ke YouTube downloads fail ho sakte hain.</blockquote>"
        )

    file_details = []
    total_entries = 0
    all_yt_ok = True

    for fpath in files:
        try:
            size = os.path.getsize(fpath)
            mtime = os.path.getmtime(fpath)
            modified = datetime.datetime.fromtimestamp(mtime).strftime("%d %b %H:%M")

            with open(fpath, "r", errors="ignore") as f:
                content = f.read()

            info = _analyze_cookie_content(content)
            if not info["yt_found"]:
                all_yt_ok = False

            total_entries += info["entry_count"]
            fname = os.path.basename(fpath)
            icon = "✅" if info["yt_found"] else "⚠️"
            file_details.append(
                f"{icon} <code>{fname}</code>\n"
                f"   📊 {info['entry_count']} entries | {size:,}B | 🕐 {modified}"
            )
        except Exception as e:
            file_details.append(f"❌ <code>{os.path.basename(fpath)}</code> — Error: {e}")

    files_text = "\n\n".join(file_details)
    overall = "✅ Ready — YouTube downloads kaam karenge!" if all_yt_ok else "⚠️ YouTube cookies missing — check karo!"
    memory_count = len(yt.cookies) if hasattr(yt, 'cookies') else 0

    await message.reply_text(
        f"<blockquote><b>🍪 Cookie Status</b>\n\n"
        f"📂 Disk files: <b>{len(files)}</b>\n"
        f"🧠 Memory mein loaded: <b>{memory_count}</b>\n"
        f"📊 Total entries: <b>{total_entries}</b>\n"
        f"Status: {overall}\n\n"
        f"<b>Files:</b>\n{files_text}\n\n"
        f"• /scookurl &lt;url&gt; — URL se instant load\n"
        f"• /scook — file upload karo\n"
        f"• /dcook — delete karo\n"
        f"• /tcook — env URL test karo</blockquote>"
    )


# ─── /dcook — Delete cookies INSTANTLY ───────────────────────────────────────
@app.on_message(filters.command(["dcook", "delcookies"]) & filters.private)
async def del_cookies_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner_or_sudo(message.from_user.id):
        return await message.reply_text("<blockquote>❌ Owner/Sudo only command.</blockquote>")

    files = _all_cookie_files()

    if not files:
        return await message.reply_text("<blockquote>ℹ️ Koi cookie file nahi hai delete karne ke liye.</blockquote>")

    args = message.text.split()

    if len(args) > 1:
        target = args[1].strip()
        if not target.endswith(".txt"):
            target = target + ".txt"
        target_path = f"{COOKIES_DIR}/{target}"

        if not os.path.exists(target_path):
            available = "\n".join(f"• <code>{os.path.basename(f)}</code>" for f in files)
            return await message.reply_text(
                f"<blockquote>❌ File nahi mili: <code>{target}</code>\n\n"
                f"<b>Available files:</b>\n{available}\n\n"
                f"Use /ccook to see all files.</blockquote>"
            )
        try:
            os.remove(target_path)
            _reload_yt_cookies_instant()
            remaining = len(_all_cookie_files())
            return await message.reply_text(
                f"<blockquote>🗑 <b>Deleted! (Instant Effect)</b>\n\n"
                f"File: <code>{target}</code>\n"
                f"📂 Remaining: {remaining} file(s)\n"
                f"⚡ Bot ne turant naye cookies load kar liye!\n"
                f"🔄 <b>Restart ki zaroorat nahi!</b></blockquote>"
            )
        except Exception as e:
            return await message.reply_text(f"<blockquote>❌ Delete failed: {e}</blockquote>")

    deleted = 0
    failed = 0
    for fpath in files:
        try:
            os.remove(fpath)
            deleted += 1
        except Exception:
            failed += 1

    _reload_yt_cookies_instant()

    msg = (
        f"<blockquote>🗑 <b>Saari Cookies Delete! (Instant Effect)</b>\n\n"
        f"✅ Deleted: {deleted} file(s)"
    )
    if failed:
        msg += f"\n❌ Failed: {failed} file(s)"
    msg += (
        f"\n⚡ Bot turant update ho gaya!\n"
        f"🔄 <b>Restart ki zaroorat nahi!</b>\n\n"
        f"Nai cookies chahiye? Use:\n"
        f"<code>/scookurl &lt;url&gt;</code></blockquote>"
    )
    await message.reply_text(msg)


# ─── /lcook — List cookie files ───────────────────────────────────────────────
@app.on_message(filters.command(["lcook", "listcookies"]) & filters.private)
async def list_cookies_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner_or_sudo(message.from_user.id):
        return await message.reply_text("<blockquote>❌ Owner/Sudo only command.</blockquote>")

    files = _all_cookie_files()
    if not files:
        return await message.reply_text("<blockquote>ℹ️ Koi cookie file nahi hai.</blockquote>")

    lines = ["<blockquote><b>📂 Cookie Files</b>\n"]
    for i, fpath in enumerate(files, 1):
        fname = os.path.basename(fpath)
        size = os.path.getsize(fpath) if os.path.exists(fpath) else 0
        lines.append(f"{i}. <code>{fname}</code> — {size:,}B")
    lines.append(f"\n<b>Total:</b> {len(files)} file(s)")
    lines.append("\nTo delete: <code>/dcook filename.txt</code></blockquote>")

    await message.reply_text("\n".join(lines))


# ─── /tcook — Test COOKIE_URL from env ───────────────────────────────────────
@app.on_message(filters.command(["tcook", "testcookies"]) & filters.private)
async def test_cookies_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner_or_sudo(message.from_user.id):
        return await message.reply_text("<blockquote>❌ Owner/Sudo only command.</blockquote>")

    status = await message.reply_text("<blockquote>🔍 COOKIE_URL env se test kar raha hun...</blockquote>")

    urls = config.COOKIES_URL

    if not urls:
        return await status.edit_text(
            "<blockquote>⚠️ <b>COOKIE_URL set nahi hai!</b>\n\n"
            "Railway env mein <code>COOKIE_URL</code> variable add karo.\n\n"
            "<b>Ya direct URL se load karo:</b>\n"
            "<code>/scookurl https://batbin.de/raw/XXXX</code></blockquote>"
        )

    results = []
    all_ok = True

    for i, original_url in enumerate(urls, 1):
        raw_url = yt._to_raw_url(original_url) if hasattr(yt, "_to_raw_url") else original_url
        result_lines = [f"<b>URL {i}:</b> <code>{original_url}</code>"]

        content, err = await _download_cookies_from_url(original_url)
        if err:
            result_lines.append(f"❌ {err}")
            all_ok = False
        else:
            info = _analyze_cookie_content(content)
            result_lines.append(f"✅ Reachable | 📊 {info['entry_count']} entries")
            result_lines.append(f"{'✅' if info['yt_found'] else '❌'} YouTube cookies: {'Found!' if info['yt_found'] else 'NOT found!'}")
            if not info["yt_found"]:
                all_ok = False

        results.append("\n".join(result_lines))

    sep = "\n\n─────────────────\n\n"
    final_text = sep.join(results)
    overall_icon = "✅" if all_ok else "❌"
    overall_text = "Saari URLs theek hain!" if all_ok else "Kuch URLs mein problem hai!"

    await status.edit_text(
        f"<blockquote><b>🧪 Cookie URL Test</b>\n\n"
        f"{final_text}\n\n"
        f"─────────────────\n"
        f"{overall_icon} <b>Overall:</b> {overall_text}\n\n"
        f"• /ccook — loaded files check\n"
        f"• /scookurl &lt;url&gt; — instant load from URL</blockquote>"
    )
