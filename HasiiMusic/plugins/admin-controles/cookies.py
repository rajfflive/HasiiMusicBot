# ==============================================================================
# cookies.py - YouTube Cookie Management
# Commands: /scook (set), /ccook (check), /dcook (delete)
# ==============================================================================

import os
import glob
import datetime

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
        # Unique filename — overwrite nahi hoga purana
        import random
        fname = f"cookie{random.randint(10000, 99999)}.txt"
        fpath = f"{COOKIES_DIR}/{fname}"

        await app.download_media(doc, file_name=fpath)

        if not os.path.exists(fpath) or os.path.getsize(fpath) < 50:
            os.remove(fpath)
            return await status.edit_text(
                "<blockquote>❌ Invalid cookie file. File too small or empty.</blockquote>"
            )

        # Validate cookie format
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

    # Check each file
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
        f"• /dcook — delete all cookies</blockquote>"
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

    # Check if specific file mentioned
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

    # Delete ALL cookie files
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
