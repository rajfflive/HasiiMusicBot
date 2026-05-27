import asyncio
import importlib
import os
import sys
import glob
import time

from pyrogram import idle

if sys.platform != "win32":
    try:
        import resource
        _soft, _hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        _target = min(65536, _hard)
        if _soft < _target:
            resource.setrlimit(resource.RLIMIT_NOFILE, (_target, _hard))
    except Exception:
        pass

from HasiiMusic import (tune, app, config, db, logger, stop, tasks, userbot, yt)
from HasiiMusic.plugins import all_modules

COOKIE_REFRESH_HOURS = 12
DISK_CLEANUP_HOURS = 6
MAX_DOWNLOAD_AGE_HOURS = 24


async def _notify(text: str):
    try:
        if config.LOGGER_ID:
            await app.send_message(config.LOGGER_ID, text, parse_mode="html")
    except Exception:
        pass


async def auto_refresh_cookies():
    while True:
        await asyncio.sleep(COOKIE_REFRESH_HOURS * 60 * 60)
        if not config.COOKIES_URL:
            continue
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
            if yt.cookies:
                logger.info(f"🍪 Cookie auto-refresh done: {len(yt.cookies)} file(s)")
                await _notify(
                    f"<blockquote><b>🍪 Cookie Auto-Refresh ✅</b></blockquote>\n\n"
                    f"<blockquote>Deleted: <b>{deleted}</b> old file(s)\n"
                    f"Loaded: <b>{len(yt.cookies)}</b> new file(s)\n"
                    f"Next refresh in: <b>{COOKIE_REFRESH_HOURS}h</b></blockquote>"
                )
            else:
                logger.error("❌ Cookie auto-refresh failed — no cookies loaded!")
                await _notify(
                    "<blockquote><b>⚠️ Cookie Refresh Failed!</b></blockquote>\n\n"
                    "<blockquote>Cookies download nahi huin!\n"
                    "Fix: <code>/setcookies &lt;url&gt;</code></blockquote>"
                )
        except Exception as e:
            logger.error(f"Cookie auto-refresh error: {e}")
            await _notify(
                f"<blockquote><b>❌ Cookie Refresh Error</b></blockquote>\n\n"
                f"<blockquote>{str(e)}</blockquote>"
            )


async def auto_disk_cleanup():
    while True:
        await asyncio.sleep(DISK_CLEANUP_HOURS * 60 * 60)
        try:
            now = time.time()
            cleaned = 0
            freed_mb = 0.0
            downloads_dir = "downloads"
            if os.path.exists(downloads_dir):
                for f in glob.glob(f"{downloads_dir}/*"):
                    if os.path.isfile(f):
                        age_hours = (now - os.path.getmtime(f)) / 3600
                        if age_hours > MAX_DOWNLOAD_AGE_HOURS:
                            size = os.path.getsize(f) / (1024 * 1024)
                            os.remove(f)
                            cleaned += 1
                            freed_mb += size
            if cleaned > 0:
                logger.info(f"🧹 Disk cleanup: removed {cleaned} files ({freed_mb:.1f} MB freed)")
                await _notify(
                    f"<blockquote><b>🧹 Auto Disk Cleanup</b></blockquote>\n\n"
                    f"<blockquote>Removed: <b>{cleaned}</b> old file(s)\n"
                    f"Freed: <b>{freed_mb:.1f} MB</b></blockquote>"
                )
        except Exception as e:
            logger.error(f"Disk cleanup error: {e}")


async def main():
    try:
        await db.connect()
        await app.boot()
        await userbot.boot()
        await tune.boot()

        failed_plugins = []
        for module in all_modules:
            try:
                importlib.import_module(f"HasiiMusic.plugins.{module}")
            except Exception as e:
                logger.error(f"Failed to load plugin {module}: {e}", exc_info=True)
                failed_plugins.append(module)
        logger.info(f"🔌 Plugins: {len(all_modules) - len(failed_plugins)}/{len(all_modules)} loaded.")

        if config.COOKIES_URL:
            try:
                await yt.save_cookies(config.COOKIES_URL)
                if yt.cookies:
                    logger.info(f"🍪 Cookies loaded: {len(yt.cookies)} file(s)")
                else:
                    logger.warning("⚠️ COOKIE_URL set hai lekin cookies load nahi huin!")
                    await _notify(
                        "<blockquote><b>⚠️ Cookie Warning</b></blockquote>\n\n"
                        "<blockquote>COOKIE_URL set hai but cookies load nahi huin!\n"
                        "Fix: <code>/setcookies &lt;url&gt;</code></blockquote>"
                    )
            except Exception as e:
                logger.error(f"Cookie load error: {e}")
        else:
            logger.warning("⚠️ COOKIE_URL not set — YouTube might fail!")

        if config.COOKIES_URL:
            t1 = asyncio.create_task(auto_refresh_cookies())
            tasks.append(t1)
            logger.info(f"⏰ Cookie auto-refresh started (every {COOKIE_REFRESH_HOURS}h)")

        t2 = asyncio.create_task(auto_disk_cleanup())
        tasks.append(t2)
        logger.info(f"🧹 Disk cleanup started (every {DISK_CLEANUP_HOURS}h)")

        sudoers = await db.get_sudoers()
        app.sudoers.update(sudoers)
        app.sudo_filter.update(sudoers)
        app.bl_users.update(await db.get_blacklisted())
        logger.info(f"👑 Sudo users: {len(app.sudoers)}")

        await _notify(
            f"<blockquote><b>🎵 {app.name} Started! ✅</b></blockquote>\n\n"
            f"<blockquote>"
            f"🔌 Plugins: <b>{len(all_modules) - len(failed_plugins)}/{len(all_modules)}</b>\n"
            f"🍪 Cookies: <b>{len(yt.cookies)}</b> file(s)\n"
            f"👑 Sudo users: <b>{len(app.sudoers)}</b>\n"
            f"⏰ Cookie refresh: every <b>{COOKIE_REFRESH_HOURS}h</b>\n"
            f"🧹 Disk cleanup: every <b>{DISK_CLEANUP_HOURS}h</b>"
            f"</blockquote>"
        )

        logger.info("\n🎉 Bot started! Ready to play music! 🎵\n")

        try:
            await idle()
        except KeyboardInterrupt:
            logger.info("Stop signal received...")
        except Exception as e:
            logger.error(f"Idle error: {e}", exc_info=True)

        await stop()

    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except SystemExit as e:
        logger.error(f"System exit: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        try:
            if loop.is_running():
                loop.stop()
        except Exception:
            pass
