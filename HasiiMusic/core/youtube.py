import os
import re
import glob
import time
import yt_dlp
import random
import asyncio
import aiohttp
from dataclasses import replace
from pathlib import Path
from typing import Optional, Union

from pyrogram import enums, types
from py_yt import Playlist, VideosSearch
from HasiiMusic import config, logger
from HasiiMusic.helpers import Track, utils

# ─── User-Agent Pool (rotate to avoid fingerprinting) ───────────────────────
USER_AGENTS = [
    # iOS Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    # Android Chrome
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    # Desktop Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.6367.60 Safari/537.36",
]
IOS_UA = USER_AGENTS[0]

COOKIE_FAIL_PHRASES = [
    "sign in to confirm",
    "bot detection",
    "video unavailable",
    "this video is unavailable",
    "age-restricted",
    "age restricted",
    "private video",
    "confirm you",
    "http error 429",
    "too many requests",
    "blocked",
    "access denied",
    "403",
    "download failed",
    "precondition check failed",
    "not available in your country",
    "region",
]

# ─── Invidious Instances (updated & verified 2025) ──────────────────────────
INVIDIOUS_INSTANCES = [
    "https://inv.nadeko.net",
    "https://invidious.privacydev.net",
    "https://yt.artemislena.eu",
    "https://invidious.lunar.icu",
    "https://iv.datura.network",
    "https://invidious.flokinet.to",
    "https://invidious.tiekoetter.com",
    "https://invidious.io.lol",
    "https://invidious.fdn.fr",
    "https://invidious.perennialte.ch",
    "https://vid.puffyan.us",
    "https://invidious.nerdvpn.de",
    "https://yt.cdaut.de",
    "https://invidious.drgns.space",
    "https://yewtu.be",
]


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies: list[str] = []
        self.checked = False
        self.warned = False
        self.cookies_expired = False
        self.last_cookie_alert: float = 0.0
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|live/|embed/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.search_cache: dict = {}
        self._download_semaphore = asyncio.Semaphore(5)
        self._max_video_height = getattr(config, "VIDEO_MAX_HEIGHT", 1080)
        self._ua_index = 0

    def _next_ua(self) -> str:
        ua = USER_AGENTS[self._ua_index % len(USER_AGENTS)]
        self._ua_index += 1
        return ua

    def _locate_download_file(self, video_id: str, video: bool = False) -> Optional[str]:
        candidates = sorted([
            p for p in glob.glob(f"downloads/{video_id}*")
            if not p.endswith((".part", ".ytdl", ".info.json", ".temp"))
        ])
        video_exts = {".mp4", ".mkv", ".webm", ".mov"}
        audio_exts = {".m4a", ".webm", ".opus", ".mp3", ".ogg", ".wav", ".flac"}
        if video:
            for p in candidates:
                if not os.path.isdir(p) and Path(p).suffix.lower() in video_exts:
                    return p
        else:
            for p in candidates:
                if not os.path.isdir(p) and Path(p).suffix.lower() in audio_exts:
                    return p
            for p in candidates:
                if not os.path.isdir(p) and Path(p).suffix.lower() in {".mp4", ".mkv", ".mov"}:
                    return p
        for p in candidates:
            if not os.path.isdir(p):
                return p
        return None

    def _is_block_error(self, err: str) -> bool:
        return any(p in err.lower() for p in COOKIE_FAIL_PHRASES)

    async def _alert_owner(self, reason: str = ""):
        now = time.time()
        if now - self.last_cookie_alert < 3600:
            return
        self.last_cookie_alert = now
        self.cookies_expired = True
        # Always log to console
        logger.warning(
            f"[YouTube] ⚠️ Block/Cookie expire detected! Reason: {reason or 'Unknown'}. "
            "Bot is using Invidious fallback. Send /setcookies <url> to fix."
        )
        try:
            from HasiiMusic import app
            if config.LOGGER_ID:
                reason_line = f"\n📌 <b>Error:</b> <code>{reason[:200]}</code>" if reason else ""
                await app.send_message(
                    config.LOGGER_ID,
                    "<blockquote expandable>"
                    "<b>⚠️ YouTube Block / Cookie Expire!</b>\n\n"
                    "YouTube direct download fail ho gaya.\n"
                    "Bot ab <b>Invidious fallback</b> se play kar raha hai."
                    f"{reason_line}\n\n"
                    "<b>🔧 Fix Karo:</b>\n"
                    "1. PC pe YouTube login karo\n"
                    "2. Nayi cookies export karo (Netscape format)\n"
                    "3. <code>/setcookies &lt;url&gt;</code> bhejo\n\n"
                    "⚡ Jab tak fix nahi hota, Invidious se play hoga."
                    "</blockquote>",
                    parse_mode="html",
                )
        except Exception as e:
            logger.error(f"[YouTube] Failed to alert owner: {e}")

    def get_cookies(self) -> Optional[str]:
        if not self.checked:
            try:
                os.makedirs("HasiiMusic/cookies", exist_ok=True)
                self.cookies = [
                    f for f in os.listdir("HasiiMusic/cookies")
                    if f.endswith(".txt")
                ]
            except Exception as e:
                logger.error(f"[YouTube] Cookie folder error: {e}")
            self.checked = True

        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning(
                    "[YouTube] ⚠️ No cookies found in HasiiMusic/cookies/. "
                    "Invidious fallback is active. Send /setcookies <url> to add cookies."
                )
            return None

        chosen = random.choice(self.cookies)
        logger.debug(f"[YouTube] Using cookie: {chosen}")
        return f"HasiiMusic/cookies/{chosen}"

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info(f"[YouTube] Downloading {len(urls)} cookie file(s)...")
        os.makedirs("HasiiMusic/cookies", exist_ok=True)
        saved = 0
        for url in urls:
            try:
                path = f"HasiiMusic/cookies/cookie{random.randint(10000, 99999)}.txt"
                link = url.replace("batbin.me/", "batbin.me/raw/") \
                    if ("batbin.me" in url and "/raw/" not in url) else url
                async with aiohttp.ClientSession() as s:
                    async with s.get(link, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status != 200:
                            logger.error(f"[YouTube] Cookie HTTP {resp.status} — {url}")
                            continue
                        content = await resp.read()
                        if len(content) < 50:
                            logger.error(f"[YouTube] Cookie too small ({len(content)} bytes) — {url}")
                            continue
                        with open(path, "wb") as fw:
                            fw.write(content)
                        name = os.path.basename(path)
                        if name not in self.cookies:
                            self.cookies.append(name)
                        self.cookies_expired = False
                        self.warned = False
                        self.last_cookie_alert = 0.0
                        saved += 1
                        logger.info(f"[YouTube] ✅ Cookie saved: {name} ({len(content)} bytes)")
            except Exception as e:
                logger.error(f"[YouTube] Cookie download error for {url}: {e}")
        self.checked = True
        if saved:
            logger.info(f"[YouTube] ✅ {saved} cookie(s) saved and ready.")
        else:
            logger.warning("[YouTube] ❌ No cookies were saved! Check the URLs.")

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def url(self, message_1: types.Message) -> Optional[str]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        link = None
        for message in messages:
            text = message.text or message.caption or ""
            if message.entities:
                for entity in message.entities:
                    if entity.type == enums.MessageEntityType.URL:
                        link = text[entity.offset: entity.offset + entity.length]
                        break
            if message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == enums.MessageEntityType.TEXT_LINK:
                        link = entity.url
                        break
        if link:
            return link.split("&si")[0].split("?si")[0]
        return None

    async def search(self, query: str, m_id: int) -> Optional[Track]:
        current_time = asyncio.get_running_loop().time()
        if query in self.search_cache:
            cached, ts = self.search_cache[query]
            if current_time - ts < 600:
                fresh = replace(cached)
                fresh.message_id = m_id
                fresh.file_path = None
                fresh.user = None
                fresh.time = 0
                fresh.video = False
                return fresh
        try:
            results = await VideosSearch(query, limit=1).next()
        except Exception as e:
            logger.warning(f"[YouTube] Search failed '{query}': {e}")
            return None
        if results and results["result"]:
            data = results["result"][0]
            duration = data.get("duration")
            is_live = duration is None or duration == "LIVE"
            track = Track(
                id=data.get("id"),
                channel_name=data.get("channel", {}).get("name"),
                duration=duration if not is_live else "LIVE",
                duration_sec=0 if is_live else utils.to_seconds(duration),
                message_id=m_id,
                title=data.get("title")[:25],
                thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                url=data.get("link"),
                view_count=data.get("viewCount", {}).get("short"),
                is_live=is_live,
            )
            self.search_cache[query] = (track, current_time)
            if len(self.search_cache) > 100:
                oldest = min(self.search_cache, key=lambda k: self.search_cache[k][1])
                del self.search_cache[oldest]
            return replace(track)
        return None

    async def playlist(self, limit: int, user: str, url: str) -> list[Track]:
        try:
            plist = await Playlist.get(url)
            if not plist or "videos" not in plist or not plist["videos"]:
                return []
            tracks = []
            for data in plist["videos"][:limit]:
                try:
                    thumbnails = data.get("thumbnails", [])
                    thumb = thumbnails[-1].get("url", "").split("?")[0] if thumbnails else ""
                    link = data.get("link", "")
                    if "&list=" in link:
                        link = link.split("&list=")[0]
                    tracks.append(Track(
                        id=data.get("id", ""),
                        channel_name=data.get("channel", {}).get("name", ""),
                        duration=data.get("duration", "0:00"),
                        duration_sec=utils.to_seconds(data.get("duration", "0:00")),
                        title=data.get("title", "Unknown")[:25],
                        thumbnail=thumb,
                        url=link,
                        user=user,
                        view_count="",
                    ))
                except Exception:
                    continue
            return tracks
        except KeyError:
            raise Exception("Failed to parse playlist.")
        except Exception:
            raise

    def _make_ydl_opts(self, cookie: Optional[str] = None, ua: Optional[str] = None) -> dict:
        opts: dict = {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
            "noplaylist": True,
            "sleep_interval_requests": 1,
            "sleep_interval": 1,
            "max_sleep_interval": 3,
            "extractor_retries": 3,
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 5,
            "user_agent": ua or self._next_ua(),
            # ── Key fix: use multiple player clients in priority order ──
            "extractor_args": {
                "youtube": {
                    "player_client": [
                        "tv_embedded",   # most reliable bypass
                        "ios",
                        "android",
                        "web_creator",
                        "mweb",
                        "web",
                    ],
                    "player_skip": ["webpage"],
                }
            },
            "http_headers": {
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        }
        if cookie:
            opts["cookiefile"] = cookie
        proxy = os.environ.get("YT_PROXY", "").strip()
        if proxy:
            opts["proxy"] = proxy
        return opts

    def _run_download(
        self, url: str, ydl_opts: dict, video_id: str, video: bool
    ) -> tuple[Optional[str], Optional[str]]:
        inst = None
        try:
            inst = yt_dlp.YoutubeDL(ydl_opts)
            inst.extract_info(url, download=True)
            time.sleep(0.5)
            return self._locate_download_file(video_id, video=video), None
        except yt_dlp.utils.DownloadError as ex:
            recovered = self._locate_download_file(video_id, video=video)
            if recovered:
                return recovered, None
            return None, str(ex)
        except Exception as ex:
            return None, str(ex)
        finally:
            if inst:
                try:
                    inst.close()
                except Exception:
                    pass

    def _run_extract_url(self, url: str, ydl_opts: dict) -> tuple[Optional[str], Optional[str]]:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None, "No info"
                direct = info.get("url")
                if direct:
                    return direct, None
                for fmt in info.get("formats", []):
                    if fmt.get("acodec") != "none" and fmt.get("url"):
                        return fmt["url"], None
                return info.get("manifest_url"), None
            except Exception as ex:
                return None, str(ex)

    async def _invidious_audio_url(self, video_id: str) -> Optional[str]:
        shuffled = random.sample(INVIDIOUS_INSTANCES, len(INVIDIOUS_INSTANCES))
        for instance in shuffled:
            try:
                api = f"{instance}/api/v1/videos/{video_id}?fields=adaptiveFormats,formatStreams"
                async with aiohttp.ClientSession() as s:
                    async with s.get(
                        api,
                        timeout=aiohttp.ClientTimeout(total=12),
                        headers={"User-Agent": IOS_UA},
                    ) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                best_url: Optional[str] = None
                best_bitrate = 0
                for fmt in data.get("adaptiveFormats", []):
                    if not fmt.get("type", "").startswith("audio/"):
                        continue
                    raw = fmt.get("url", "")
                    if not raw:
                        continue
                    if not raw.startswith("http"):
                        raw = instance + raw
                    bitrate = int(fmt.get("bitrate", 0))
                    if bitrate > best_bitrate:
                        best_bitrate = bitrate
                        best_url = raw
                if best_url:
                    logger.info(f"[YouTube] ✅ Invidious audio OK [{instance}]: {video_id}")
                    return best_url
                for fmt in data.get("formatStreams", []):
                    raw = fmt.get("url", "")
                    if raw:
                        if not raw.startswith("http"):
                            raw = instance + raw
                        logger.info(f"[YouTube] ✅ Invidious stream OK [{instance}]: {video_id}")
                        return raw
            except asyncio.TimeoutError:
                logger.debug(f"[YouTube] Invidious timeout: {instance}")
                continue
            except Exception as e:
                logger.debug(f"[YouTube] Invidious {instance} error: {e}")
                continue
        logger.error(f"[YouTube] ❌ All Invidious instances failed for: {video_id}")
        return None

    async def _invidious_video_url(self, video_id: str) -> Optional[str]:
        shuffled = random.sample(INVIDIOUS_INSTANCES, len(INVIDIOUS_INSTANCES))
        for instance in shuffled:
            try:
                api = f"{instance}/api/v1/videos/{video_id}?fields=adaptiveFormats,formatStreams"
                async with aiohttp.ClientSession() as s:
                    async with s.get(
                        api,
                        timeout=aiohttp.ClientTimeout(total=12),
                        headers={"User-Agent": IOS_UA},
                    ) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                for fmt in data.get("formatStreams", []):
                    raw = fmt.get("url", "")
                    if raw:
                        if not raw.startswith("http"):
                            raw = instance + raw
                        return raw
            except Exception:
                continue
        return None

    async def _invidious_live_url(self, video_id: str) -> Optional[str]:
        shuffled = random.sample(INVIDIOUS_INSTANCES, len(INVIDIOUS_INSTANCES))
        for instance in shuffled:
            try:
                api = f"{instance}/api/v1/videos/{video_id}?fields=hlsUrl,dashManifestUrl"
                async with aiohttp.ClientSession() as s:
                    async with s.get(api, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                hls = data.get("hlsUrl") or data.get("dashManifestUrl")
                if hls:
                    if not hls.startswith("http"):
                        hls = instance + hls
                    return hls
            except Exception:
                continue
        return None

    async def download(
        self, video_id: str, is_live: bool = False, video: bool = False
    ) -> Optional[str]:
        url = self.base + video_id

        # ── Live Stream ────────────────────────────────────────────────────
        if is_live:
            cookie = self.get_cookies()
            opts = {**self._make_ydl_opts(cookie), "format": "bestaudio/best"}
            try:
                result, err = await asyncio.wait_for(
                    asyncio.to_thread(self._run_extract_url, url, opts), timeout=30
                )
            except asyncio.TimeoutError:
                result, err = None, "timeout"
            if result:
                return result

            # Try without cookies
            if cookie:
                opts2 = {**self._make_ydl_opts(), "format": "bestaudio/best"}
                try:
                    result2, _ = await asyncio.wait_for(
                        asyncio.to_thread(self._run_extract_url, url, opts2), timeout=25
                    )
                    if result2:
                        return result2
                except asyncio.TimeoutError:
                    pass

            asyncio.create_task(self._alert_owner(err or "live stream extract failed"))
            return await self._invidious_live_url(video_id)

        # ── Check existing cached download ─────────────────────────────────
        existing = [f for f in glob.glob(f"downloads/{video_id}.*") if not f.endswith(".part")]
        if video:
            for f in existing:
                if Path(f).suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}:
                    logger.debug(f"[YouTube] Cache hit (video): {f}")
                    return f
        else:
            for f in existing:
                if Path(f).suffix.lower() in {".m4a", ".webm", ".opus", ".mp3", ".ogg", ".wav", ".flac"}:
                    logger.debug(f"[YouTube] Cache hit (audio): {f}")
                    return f
            for f in existing:
                if Path(f).suffix.lower() in {".mp4", ".mkv", ".mov"}:
                    logger.debug(f"[YouTube] Cache hit (video→audio): {f}")
                    return f

        Path("downloads").mkdir(parents=True, exist_ok=True)

        async with self._download_semaphore:
            cookie = self.get_cookies()
            base = {
                **self._make_ydl_opts(cookie),
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "overwrites": False,
                "continuedl": True,
                "noprogress": True,
                "concurrent_fragment_downloads": 4,
                "http_chunk_size": 524288,
            }
            if video:
                h = f"[height<={self._max_video_height}]" if self._max_video_height else ""
                ydl_opts = {
                    **base,
                    "format": f"bestvideo[ext=mp4]{h}+bestaudio[ext=m4a]/bestvideo{h}+bestaudio/best",
                    "merge_output_format": "mp4",
                    "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
                }
            else:
                ydl_opts = {
                    **base,
                    "format": "bestaudio[ext=m4a]/bestaudio[acodec=opus]/bestaudio/best",
                    "postprocessors": [],
                }

            # ── Attempt 1: with cookies ────────────────────────────────────
            logger.info(f"[YouTube] Attempt 1 (cookie={'yes' if cookie else 'no'}): {video_id}")
            result, err = await asyncio.to_thread(
                self._run_download, url, ydl_opts, video_id, video
            )
            if result:
                logger.info(f"[YouTube] ✅ Download OK (attempt 1): {video_id}")
                return result

            logger.warning(f"[YouTube] Attempt 1 failed [{video_id}]: {str(err)[:120]}")

            # ── Attempt 2: without cookies, rotated UA ─────────────────────
            if cookie:
                no_cookie_opts = {
                    **{k: v for k, v in ydl_opts.items() if k != "cookiefile"},
                    "user_agent": self._next_ua(),
                }
                logger.info(f"[YouTube] Attempt 2 (no-cookie, rotated UA): {video_id}")
                result2, err2 = await asyncio.to_thread(
                    self._run_download, url, no_cookie_opts, video_id, video
                )
                if result2:
                    logger.info(f"[YouTube] ✅ Download OK (attempt 2, no-cookie): {video_id}")
                    return result2
                logger.warning(f"[YouTube] Attempt 2 failed [{video_id}]: {str(err2)[:80]}")

            # ── Attempt 3: tv_embedded client only (often bypasses bot check) ──
            tv_opts = {
                **{k: v for k, v in ydl_opts.items() if k not in ("cookiefile",)},
                "user_agent": USER_AGENTS[2],  # Desktop Chrome
                "extractor_args": {
                    "youtube": {
                        "player_client": ["tv_embedded"],
                        "player_skip": ["webpage"],
                    }
                },
            }
            if cookie:
                tv_opts["cookiefile"] = cookie
            logger.info(f"[YouTube] Attempt 3 (tv_embedded client): {video_id}")
            result3, err3 = await asyncio.to_thread(
                self._run_download, url, tv_opts, video_id, video
            )
            if result3:
                logger.info(f"[YouTube] ✅ Download OK (attempt 3, tv_embedded): {video_id}")
                return result3
            logger.warning(f"[YouTube] Attempt 3 failed [{video_id}]: {str(err3)[:80]}")

            # ── All yt-dlp attempts failed → alert owner + use Invidious ──
            first_err = err or err2 or err3 or "unknown"
            asyncio.create_task(self._alert_owner(first_err))

            logger.info(f"[YouTube] Trying Invidious fallback: {video_id}")
            inv = await (
                self._invidious_video_url(video_id)
                if video
                else self._invidious_audio_url(video_id)
            )
            if inv:
                logger.info(f"[YouTube] ✅ Invidious fallback success: {video_id}")
                return inv

            logger.error(f"[YouTube] ❌ All methods failed for: {video_id} | Error: {first_err[:150]}")
            return None
