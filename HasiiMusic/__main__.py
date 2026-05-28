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

from HasiiMusic import tune, app, config, db, logger, stop, tasks, userbot, yt
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
        await asyncio.sleep(COOKIE_REFRESH_HOURS * 3600)
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
            yt.cookies_expired = False      # ← ab __init__ mein hai, crash nahi hoga
            yt.last_cookie_alert = 0.0      # ← ab __init__ mein hai, crash nahi hoga
            await yt.save_cookies(config.COOKIES_URL)
            if yt.cookies:
                await _notify(
                    f"<blockquote><b>🍪 Cookie Auto-Refresh ✅</b></blockquote>\n\n"
                    f"<blockquote>Old deleted: <b>{deleted}</b>\n"
                    f"New loaded: <b>{len(yt.cookies)}</b>\n"
                    f"Next: <b>{COOKIE_REFRESH_HOURS}h baad</b></blockquote>"
                )
            else:
                await _notify(
                    "<blockquote><b>⚠️ Cookie Refresh Failed!</b></blockquote>\n\n"
                    "<blockquote>Cookies nahi aai.\n"
                    "Bot bina cookies ke try karega.\n"
                    "Fix: <code>/scook</code> se nai cookies upload karo</blockquote>"
                )
        except Exception as e:
            logger.error(f"Cookie refresh error: {e}")


async def auto_disk_cleanup():
    while True:
        await asyncio.sleep(DISK_CLEANUP_HOURS * 3600)
        try:
            now = time.time()
            cleaned = 0
            freed = 0.0
            if os.path.exists("downloads"):
                for f in glob.glob("downloads/*"):
                    if os.path.isfile(f) and (now - os.path.getmtime(f)) / 3600 > MAX_DOWNLOAD_AGE_HOURS:
                        freed += os.path.getsize(f) / (1024 * 1024)
                        os.remove(f)
                        cleaned += 1
            if cleaned > 0:
                await _notify(
                    f"<blockquote><b>🧹 Disk Cleanup</b></blockquote>\n\n"
                    f"<blockquote>Removed: <b>{cleaned}</b> files\n"
                    f"Freed: <b>{freed:.1f} MB</b></blockquote>"
                )
        except Exception as e:
            logger.error(f"Disk cleanup error: {e}")


async def main():
    try:
        await db.connect()
        await app.boot()
        await userbot.boot()
        await tune.boot()

        failed = []
        for module in all_modules:
            try:
                importlib.import_module(f"HasiiMusic.plugins.{module}")
            except Exception as e:
                logger.error(f"Plugin failed {module}: {e}", exc_info=True)
                failed.append(module)

        os.makedirs("HasiiMusic/cookies", exist_ok=True)
        os.makedirs("downloads", exist_ok=True)

        if config.COOKIES_URL:
            try:
                await yt.save_cookies(config.COOKIES_URL)
            except Exception as e:
                logger.error(f"Cookie load error: {e}")

        if config.COOKIES_URL:
            tasks.append(asyncio.create_task(auto_refresh_cookies()))
        tasks.append(asyncio.create_task(auto_disk_cleanup()))

        sudoers = await db.get_sudoers()
        app.sudoers.update(sudoers)
        app.sudo_filter.update(sudoers)
        app.bl_users.update(await db.get_blacklisted())

        await _notify(
            f"<blockquote><b>🎵 {app.name} Started ✅</b></blockquote>\n\n"
            f"<blockquote>"
            f"🔌 Plugins: <b>{len(all_modules) - len(failed)}/{len(all_modules)}</b>\n"
            f"🍪 Cookies: <b>{len(yt.cookies)}</b> file(s)\n"
            f"🚂 Platform: <b>Railway</b>\n"
            f"👑 Sudo: <b>{len(app.sudoers)}</b> users\n"
            f"⏰ Cookie refresh: every <b>{COOKIE_REFRESH_HOURS}h</b>\n"
            f"🧹 Disk cleanup: every <b>{DISK_CLEANUP_HOURS}h</b>"
            f"</blockquote>"
        )
        logger.info("Bot started!")

        try:
            await idle()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(f"Idle error: {e}", exc_info=True)

        await stop()

    except Exception as e:
        logger.error(f"Critical: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"Fatal: {e}", exc_info=True)
    finally:
        try:
            if loop.is_running():
                loop.stop()
        except Exception:
            pass
