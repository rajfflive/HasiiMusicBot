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

IOS_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
    "Mobile/15E148 Safari/604.1"
)

COOKIE_FAIL_PHRASES = [
    "sign in to confirm", "bot detection", "video unavailable",
    "this video is unavailable", "age-restricted", "private video",
    "confirm you", "http error 429", "too many requests",
    "blocked", "access denied", "403",
]

INVIDIOUS_INSTANCES = [
    "https://inv.nadeko.net",
    "https://invidious.privacydev.net",
    "https://yt.artemislena.eu",
    "https://invidious.lunar.icu",
    "https://iv.datura.network",
    "https://invidious.flokinet.to",
    "https://invidious.tiekoetter.com",
    "https://invidious.io.lol",
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

    async def _alert_owner(self):
        now = time.time()
        if now - self.last_cookie_alert < 3600:
            return
        self.last_cookie_alert = now
        self.cookies_expired = True
        try:
            from HasiiMusic import app
            if config.LOGGER_ID:
                await app.send_message(
                    config.LOGGER_ID,
                    "<blockquote><b>⚠️ YouTube Block / Cookie Expire!</b></blockquote>\n\n"
                    "<blockquote>YouTube direct fail ho raha hai.\n"
                    "Bot <b>Invidious fallback</b> se play kar raha hai.\n\n"
                    "<b>Fix:</b>\n"
                    "1. PC pe YouTube login karo\n"
                    "2. Nayi cookies export karo\n"
                    "3. <code>/setcookies &lt;url&gt;</code> bhejo</blockquote>",
                    parse_mode="html"
                )
        except Exception:
            pass

    def get_cookies(self) -> Optional[str]:
        if not self.checked:
            try:
                os.makedirs("HasiiMusic/cookies", exist_ok=True)
                for f in os.listdir("HasiiMusic/cookies"):
                    if f.endswith(".txt"):
                        self.cookies.append(f)
            except Exception:
                pass
            self.checked = True
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("No cookies — Invidious fallback active.")
            return None
        return f"HasiiMusic/cookies/{random.choice(self.cookies)}"

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("Downloading cookies...")
        os.makedirs("HasiiMusic/cookies", exist_ok=True)
        saved = 0
        for url in urls:
            try:
                path = f"HasiiMusic/cookies/cookie{random.randint(10000,99999)}.txt"
                link = url.replace("batbin.me/", "batbin.me/raw/") \
                    if ("batbin.me" in url and "/raw/" not in url) else url
                async with aiohttp.ClientSession() as s:
                    async with s.get(link, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status != 200:
                            logger.error(f"Cookie HTTP {resp.status} — {url}")
                            continue
                        content = await resp.read()
                        if len(content) < 50:
                            logger.error(f"Cookie too small — {url}")
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
                        logger.info(f"Cookie saved: {name} ({len(content)} bytes)")
            except Exception as e:
                logger.error(f"Cookie error {url}: {e}")
        self.checked = True
        logger.info(f"{saved} cookie(s) ready." if saved else "No cookies saved!")

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
            logger.warning(f"Search failed '{query}': {e}")
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

    def _make_ydl_opts(self, cookie: Optional[str] = None) -> dict:
        opts: dict = {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
            "noplaylist": True,
            "sleep_interval_requests": 1,
            "extractor_retries": 3,
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 3,
            "user_agent": IOS_UA,
            "extractor_args": {
                "youtube": {"player_client": ["ios", "mweb", "android", "web"]}
            },
        }
        if cookie:
            opts["cookiefile"] = cookie
        proxy = os.environ.get("YT_PROXY", "").strip()
        if proxy:
            opts["proxy"] = proxy
        return opts

    def _run_download(self, url: str, ydl_opts: dict, video_id: str, video: bool) -> tuple[Optional[str], Optional[str]]:
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
        for instance in INVIDIOUS_INSTANCES:
            try:
                api = f"{instance}/api/v1/videos/{video_id}?fields=adaptiveFormats,formatStreams"
                async with aiohttp.ClientSession() as s:
                    async with s.get(api, timeout=aiohttp.ClientTimeout(total=10)) as resp:
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
                    logger.info(f"Invidious audio OK [{instance}]: {video_id}")
                    return best_url
                for fmt in data.get("formatStreams", []):
                    raw = fmt.get("url", "")
                    if raw:
                        if not raw.startswith("http"):
                            raw = instance + raw
                        return raw
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.debug(f"Invidious {instance}: {e}")
                continue
        logger.error(f"All Invidious failed: {video_id}")
        return None

    async def _invidious_video_url(self, video_id: str) -> Optional[str]:
        for instance in INVIDIOUS_INSTANCES:
            try:
                api = f"{instance}/api/v1/videos/{video_id}?fields=adaptiveFormats,formatStreams"
                async with aiohttp.ClientSession() as s:
                    async with s.get(api, timeout=aiohttp.ClientTimeout(total=10)) as resp:
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
        for instance in INVIDIOUS_INSTANCES:
            try:
                api = f"{instance}/api/v1/videos/{video_id}?fields=hlsUrl,dashManifestUrl"
                async with aiohttp.ClientSession() as s:
                    async with s.get(api, timeout=aiohttp.ClientTimeout(total=10)) as resp:
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

    async def download(self, video_id: str, is_live: bool = False, video: bool = False) -> Optional[str]:
        url = self.base + video_id

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
            asyncio.create_task(self._alert_owner())
            return await self._invidious_live_url(video_id)

        existing = [f for f in glob.glob(f"downloads/{video_id}.*") if not f.endswith(".part")]
        if video:
            for f in existing:
                if Path(f).suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}:
                    return f
        else:
            for f in existing:
                if Path(f).suffix.lower() in {".m4a", ".webm", ".opus", ".mp3", ".ogg", ".wav", ".flac"}:
                    return f
            for f in existing:
                if Path(f).suffix.lower() in {".mp4", ".mkv", ".mov"}:
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

            result, err = await asyncio.to_thread(self._run_download, url, ydl_opts, video_id, video)
            if result:
                return result

            logger.warning(f"yt-dlp failed [{video_id}]: {str(err)[:100]}")

            if cookie:
                no_cookie = {k: v for k, v in ydl_opts.items() if k != "cookiefile"}
                result2, err2 = await asyncio.to_thread(self._run_download, url, no_cookie, video_id, video)
                if result2:
                    return result2
                logger.warning(f"No-cookie also failed: {str(err2)[:80]}")

            asyncio.create_task(self._alert_owner())
            logger.info(f"Trying Invidious: {video_id}")
            inv = await (self._invidious_video_url(video_id) if video else self._invidious_audio_url(video_id))
            if inv:
                logger.info(f"Invidious success: {video_id}")
                return inv

            logger.error(f"All methods failed: {video_id}")
            return None
