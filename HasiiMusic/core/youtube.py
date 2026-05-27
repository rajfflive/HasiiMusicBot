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

IOS_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.warned = False
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|live/|embed/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.search_cache = {}
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

    def get_cookies(self):
        if not self.checked:
            try:
                for f in os.listdir("HasiiMusic/cookies"):
                    if f.endswith(".txt"):
                        self.cookies.append(f)
            except Exception:
                pass
            self.checked = True
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("⚠️ No cookies found — YouTube might block downloads.")
            return None
        return f"HasiiMusic/cookies/{random.choice(self.cookies)}"

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("🍪 Downloading cookies...")
        saved_count = 0
        for url in urls:
            try:
                path = f"HasiiMusic/cookies/cookie{random.randint(10000, 99999)}.txt"
                # Only modify batbin.me URLs — keep all others as-is
                if "batbin.me" in url and "/raw/" not in url:
                    link = url.replace("batbin.me/", "batbin.me/raw/")
                else:
                    link = url
                async with aiohttp.ClientSession() as session:
                    async with session.get(link, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status != 200:
                            logger.error(f"❌ Cookie HTTP {resp.status} from {url}")
                            continue
                        content = await resp.read()
                        if not content or len(content) < 50:
                            logger.error(f"❌ Cookie file too small/empty from {url}")
                            continue
                        with open(path, "wb") as fw:
                            fw.write(content)
                        if os.path.exists(path) and os.path.getsize(path) > 0:
                            saved_count += 1
                            name = os.path.basename(path)
                            if name not in self.cookies:
                                self.cookies.append(name)
                            logger.info(f"✅ Cookie saved: {name} ({len(content)} bytes)")
            except Exception as e:
                logger.error(f"❌ Cookie error from {url}: {e}")
        self.checked = True
        if saved_count > 0:
            logger.info(f"✅ {saved_count} cookie file(s) ready.")
        else:
            logger.error("❌ No cookies saved! Check COOKIE_URL.")

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def url(self, message_1: types.Message) -> Union[str, None]:
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

    async def search(self, query: str, m_id: int) -> Track | None:
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
            logger.warning(f"⚠️ Search failed for '{query}': {e}")
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

    def _base_ydl_opts(self) -> dict:
        return {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
            "sleep_interval_requests": 1,
            "extractor_retries": 5,
            "socket_timeout": 30,
            "user_agent": IOS_UA,
            # iOS client bypasses bot detection on datacenter IPs without needing PO tokens
            "extractor_args": {"youtube": {"player_client": ["ios", "android", "web"]}},
        }

    async def download(self, video_id: str, is_live: bool = False, video: bool = False) -> Optional[str]:
        url = self.base + video_id

        if is_live:
            cookie = self.get_cookies()
            ydl_opts = {
                **self._base_ydl_opts(),
                "cookiefile": cookie,
                "format": "bestaudio/best",
                "noplaylist": True,
            }

            def _extract():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=False)
                        if not info:
                            return None
                        direct = info.get("url")
                        if direct:
                            return direct
                        for fmt in info.get("formats", []):
                            if fmt.get("acodec") != "none" and fmt.get("url"):
                                return fmt["url"]
                        return info.get("manifest_url")
                    except Exception as ex:
                        logger.error(f"Live extract failed: {ex}")
                        return None

            try:
                return await asyncio.wait_for(asyncio.to_thread(_extract), timeout=35)
            except asyncio.TimeoutError:
                logger.error(f"Live stream timed out: {video_id}")
                return None

        # Check cached files
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
            base_opts = {
                **self._base_ydl_opts(),
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "noplaylist": True,
                "overwrites": False,
                "continuedl": True,
                "noprogress": True,
                "concurrent_fragment_downloads": 4,
                "http_chunk_size": 524288,
                "retries": 3,
                "fragment_retries": 3,
                "cookiefile": cookie,
            }

            if video:
                h = f"[height<={self._max_video_height}]" if self._max_video_height else ""
                ydl_opts = {
                    **base_opts,
                    "format": f"bestvideo[ext=mp4]{h}+bestaudio[ext=m4a]/bestvideo{h}+bestaudio/best",
                    "merge_output_format": "mp4",
                    "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
                }
            else:
                ydl_opts = {
                    **base_opts,
                    "format": "bestaudio[ext=m4a]/bestaudio[acodec=opus]/bestaudio/best",
                    "postprocessors": [],
                }

            def _download():
                inst = None
                try:
                    inst = yt_dlp.YoutubeDL(ydl_opts)
                    info = inst.extract_info(url, download=True)
                    if not info:
                        return None
                    time.sleep(0.5)
                    return self._locate_download_file(video_id, video=video)
                except yt_dlp.utils.DownloadError as ex:
                    recovered = self._locate_download_file(video_id, video=video)
                    if recovered:
                        return recovered
                    logger.warning(f"⚠️ Download error {video_id}: {ex}")
                    return None
                except Exception as ex:
                    logger.warning(f"⚠️ Unexpected error {video_id}: {ex}")
                    return None
                finally:
                    if inst:
                        try:
                            inst.close()
                        except Exception:
                            pass

            return await asyncio.to_thread(_download)
