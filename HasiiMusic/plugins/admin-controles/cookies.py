# ==============================================================================
# cookies.py - YouTube Cookie Management
# Commands: /scook (set), /ccook (check), /dcook (delete), /tcook (test)
# ==============================================================================

import os
import glob
import datetime
import aiohttp

from pyrogram import filters, types
from HasiiMusic import app, config, yt

COOKIES_DIR = "HasiiMusic/cookies"
OWNER_ID = int(getattr(config, "OWNER_ID", 0))


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def _all_cookie_files() -> list[str]:
    return sorted(glob.glob(f"{COOKIES_DIR}/*.txt"))


def _reload_yt_cookies():
    """youtube instance ko naye cookies se update karo."""
    try:
        yt.cookies = []
        yt.checked = False
        yt.warned = False
        for f in os.listdir(COOKIES_DIR):
            if f.endswith(".txt"):
                yt.cookies.append(f)
        yt.checked = True
    except Exception:
        pass


# ── /scook — Set/Upload cookies ──────────────────────────────────────────────

@app.on_message(filters.command(["scook", "setcookies"]) & filters.private)
async def set_cookies_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner(message.from_user.id):
        return await message.reply_text("<blockquote>❌ Owner only command.</blockquote>")

    doc = message.document or (
        message.reply_to_message.document if message.reply_to_message else None
    )

    if not doc:
        files = _all_cookie_files()
        count = len(files)
        return await message.reply_text(
            "<blockquote><b>🍪 Set Cookies</b>\n\n"
            "Reply to a <code>cookies.txt</code> file with /scook\n"
            "or send the file with /scook caption.\n\n"
            f"📂 Current cookie files: <b>{count}</b>\n"
            "Use /ccook to check status.</blockquote>"
        )

    os.makedirs(COOKIES_DIR, exist_ok=True)
    status = await message.reply_text("<blockquote>⏳ Saving cookies...</blockquote>")

    try:
        import random
        fname = f"cookie{random.randint(10000, 99999)}.txt"
        fpath = f"{COOKIES_DIR}/{fname}"

        await app.download_media(doc, file_name=fpath)

        if not os.path.exists(fpath) or os.path.getsize(fpath) < 50:
            os.remove(fpath)
            return await status.edit_text(
                "<blockquote>❌ Invalid cookie file. File too small or empty.</blockquote>"
            )

        with open(fpath, "r", errors="ignore") as f:
            content = f.read()

        lines = [l for l in content.splitlines() if l.strip() and not l.startswith("#")]
        yt_found = any("youtube" in l or "google" in l for l in lines)
        size = os.path.getsize(fpath)

        _reload_yt_cookies()
        total = len(_all_cookie_files())

        yt_icon = "✅" if yt_found else "⚠️"
        yt_text = "YouTube cookies found" if yt_found else "YouTube cookies NOT found — might not work"

        await status.edit_text(
            f"<blockquote>✅ <b>Cookies Saved!</b>\n\n"
            f"📁 File: <code>{fname}</code>\n"
            f"📦 Size: {size:,} bytes\n"
            f"📊 Cookie entries: {len(lines)}\n"
            f"{yt_icon} {yt_text}\n\n"
            f"📂 Total cookie files: <b>{total}</b>\n"
            f"Bot is now using the new cookies.</blockquote>"
        )

    except Exception as e:
        await status.edit_text(f"<blockquote>❌ Failed to save cookies:\n<code>{e}</code></blockquote>")


# ── /ccook — Check cookies ────────────────────────────────────────────────────

@app.on_message(filters.command(["ccook", "checkcookies"]))
async def check_cookies_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner(message.from_user.id):
        return await message.reply_text("<blockquote>❌ Owner only command.</blockquote>")

    files = _all_cookie_files()

    if not files:
        return await message.reply_text(
            "<blockquote>⚠️ <b>No cookie files found!</b>\n\n"
            "Use /scook to upload a cookies.txt file.\n\n"
            "Without cookies, YouTube downloads may fail.</blockquote>"
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

            lines = [l for l in content.splitlines() if l.strip() and not l.startswith("#")]
            yt_ok = any("youtube" in l.lower() or "google" in l.lower() for l in lines)

            if not yt_ok:
                all_yt_ok = False

            total_entries += len(lines)
            fname = os.path.basename(fpath)
            icon = "✅" if yt_ok else "⚠️"
            file_details.append(
                f"{icon} <code>{fname}</code> — {len(lines)} entries, {size:,}B, updated {modified}"
            )
        except Exception as e:
            file_details.append(f"❌ <code>{os.path.basename(fpath)}</code> — Error: {e}")

    files_text = "\n".join(file_details)
    overall = "✅ Ready" if all_yt_ok else "⚠️ Check cookies — YouTube entries missing"

    await message.reply_text(
        f"<blockquote><b>🍪 Cookie Status</b>\n\n"
        f"📂 Total files: <b>{len(files)}</b>\n"
        f"📊 Total entries: <b>{total_entries}</b>\n"
        f"Status: {overall}\n\n"
        f"<b>Files:</b>\n{files_text}\n\n"
        f"• /scook — upload new cookies\n"
        f"• /dcook — delete all cookies\n"
        f"• /tcook — test COOKIE_URL from env</blockquote>"
    )


# ── /dcook — Delete cookies ───────────────────────────────────────────────────

@app.on_message(filters.command(["dcook", "delcookies"]) & filters.private)
async def del_cookies_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner(message.from_user.id):
        return

    files = _all_cookie_files()

    if not files:
        return await message.reply_text(
            "<blockquote>ℹ️ No cookie files to delete.</blockquote>"
        )

    args = message.text.split()
    if len(args) > 1:
        target = args[1].strip()
        target_path = f"{COOKIES_DIR}/{target}"
        if not os.path.exists(target_path):
            return await message.reply_text(
                f"<blockquote>❌ File not found: <code>{target}</code>\n\n"
                f"Use /ccook to see all files.</blockquote>"
            )
        try:
            os.remove(target_path)
            _reload_yt_cookies()
            remaining = len(_all_cookie_files())
            return await message.reply_text(
                f"<blockquote>🗑 Deleted: <code>{target}</code>\n"
                f"📂 Remaining cookie files: {remaining}</blockquote>"
            )
        except Exception as e:
            return await message.reply_text(f"<blockquote>❌ {e}</blockquote>")

    deleted = 0
    failed = 0
    for fpath in files:
        try:
            os.remove(fpath)
            deleted += 1
        except Exception:
            failed += 1

    _reload_yt_cookies()

    msg = f"<blockquote>🗑 <b>All cookies deleted!</b>\n\n✅ Deleted: {deleted} files"
    if failed:
        msg += f"\n❌ Failed: {failed} files"
    msg += "\n\nUse /scook to upload new cookies.</blockquote>"

    await message.reply_text(msg)


# ── /tcook — Test COOKIE_URL from Railway env ─────────────────────────────────

@app.on_message(filters.command(["tcook", "testcookies"]) & filters.private)
async def test_cookies_cmd(_, message: types.Message):
    if not message.from_user or not _is_owner(message.from_user.id):
        return await message.reply_text("<blockquote>❌ Owner only command.</blockquote>")

    status = await message.reply_text("<blockquote>🔍 Testing COOKIE_URL from env...</blockquote>")

    urls = config.COOKIES_URL

    if not urls:
        return await status.edit_text(
            "<blockquote>⚠️ <b>COOKIE_URL not set!</b>\n\n"
            "Railway env mein <code>COOKIE_URL</code> variable add karo.\n\n"
            "<b>Example:</b>\n"
            "<code>https://batbin.de/xAbCdEfG</code>\n\n"
            "Multiple URLs space se alag karo.</blockquote>"
        )

    results = []
    all_ok = True

    for i, original_url in enumerate(urls, 1):
        raw_url = yt._to_raw_url(original_url)
        result_lines = [f"<b>URL {i}:</b> <code>{original_url}</code>"]

        if raw_url != original_url:
            result_lines.append(f"🔄 Raw URL: <code>{raw_url}</code>")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(raw_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    http_status = resp.status

                    if http_status != 200:
                        result_lines.append(f"❌ HTTP {http_status} — URL accessible nahi hai")
                        all_ok = False
                        results.append("\n".join(result_lines))
                        continue

                    content = await resp.read()
                    size = len(content)
                    content_text = content.decode("utf-8", errors="ignore")

                    # Check: HTML page aayi toh URL galat hai
                    if content_text.strip().startswith("<!DOCTYPE") or content_text.strip().startswith("<html"):
                        result_lines.append(f"❌ HTML page mili — raw URL galat hai")
                        result_lines.append(f"   Batbin use karo: <code>batbin.de/raw/XXXX</code>")
                        all_ok = False
                        results.append("\n".join(result_lines))
                        continue

                    # Check: size
                    if size < 50:
                        result_lines.append(f"❌ File bahut chhoti hai ({size} bytes) — paste empty lagta hai")
                        all_ok = False
                        results.append("\n".join(result_lines))
                        continue

                    # Check: Netscape format
                    lines_all = content_text.splitlines()
                    has_netscape = any("Netscape HTTP Cookie File" in l for l in lines_all[:3])
                    cookie_lines = [l for l in lines_all if l.strip() and not l.startswith("#")]
                    yt_found = any("youtube" in l.lower() or "google" in l.lower() for l in cookie_lines)
                    google_found = any("google" in l.lower() for l in cookie_lines)

                    # Summary
                    result_lines.append(f"✅ HTTP {http_status} — Reachable")
                    result_lines.append(f"📦 Size: {size:,} bytes")
                    result_lines.append(f"📊 Cookie entries: {len(cookie_lines)}")
                    result_lines.append(f"{'✅' if has_netscape else '⚠️'} Netscape format: {'Yes' if has_netscape else 'Not detected (might still work)'}")
                    result_lines.append(f"{'✅' if yt_found else '❌'} YouTube cookies: {'Found' if yt_found else 'NOT found!'}")
                    result_lines.append(f"{'✅' if google_found else '⚠️'} Google cookies: {'Found' if google_found else 'Not found'}")

                    if not yt_found:
                        result_lines.append(f"\n⚠️ YouTube cookies nahi hain — bot download fail karega")
                        all_ok = False
                    else:
                        result_lines.append(f"\n✅ Ye URL kaam karega!")

        except aiohttp.ClientConnectorError:
            result_lines.append(f"❌ Connect nahi ho saka — URL galat ya site down hai")
            all_ok = False
        except aiohttp.ServerTimeoutError:
            result_lines.append(f"❌ Timeout — site respond nahi kar rahi (15s)")
            all_ok = False
        except Exception as e:
            result_lines.append(f"❌ Error: <code>{e}</code>")
            all_ok = False

        results.append("\n".join(result_lines))

    separator = "\n\n─────────────────\n\n"
    final_text = separator.join(results)

    overall_icon = "✅" if all_ok else "❌"
    overall_text = "Saari URLs theek hain!" if all_ok else "Kuch URLs mein problem hai — upar dekho"

    await status.edit_text(
        f"<blockquote><b>🧪 Cookie URL Test</b>\n\n"
        f"{final_text}\n\n"
        f"─────────────────\n"
        f"{overall_icon} <b>Overall:</b> {overall_text}\n\n"
        f"• /ccook — loaded files check karo\n"
        f"• /scook — file upload karo</blockquote>"
    )
