# ==============================================================================
# youtube.py - YouTube Download & Search Handler
# ==============================================================================

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
        self.cache_time = {}
        self._download_semaphore = asyncio.Semaphore(5)
        self._max_video_height = getattr(config, "VIDEO_MAX_HEIGHT", 1080)

    def _locate_download_file(self, video_id: str, video: bool = False) -> Optional[str]:
        pattern = f"downloads/{video_id}*"
        candidates = sorted([
            path for path in glob.glob(pattern)
            if not path.endswith((".part", ".ytdl", ".info.json", ".temp"))
        ])
        video_exts = {".mp4", ".mkv", ".webm", ".mov"}
        audio_exts = {".m4a", ".webm", ".opus", ".mp3", ".ogg", ".wav", ".flac"}

        if video:
            for path in candidates:
                if not os.path.isdir(path) and Path(path).suffix.lower() in video_exts:
                    return path
        else:
            for path in candidates:
                if not os.path.isdir(path) and Path(path).suffix.lower() in audio_exts:
                    return path
            for path in candidates:
                if not os.path.isdir(path) and Path(path).suffix.lower() in {".mp4", ".mkv", ".mov"}:
                    return path

        for path in candidates:
            if not os.path.isdir(path):
                return path
        return None

    def get_cookies(self) -> Optional[str]:
        if not self.checked:
            cookie_dir = "HasiiMusic/cookies"
            if os.path.isdir(cookie_dir):
                for f in os.listdir(cookie_dir):
                    if f.endswith(".txt"):
                        self.cookies.append(f)
            self.checked = True

        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("Cookies are missing; downloads might fail.")
            return None

        return f"HasiiMusic/cookies/{random.choice(self.cookies)}"

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("🍪 Saving cookies from urls...")
        saved_count = 0
        for url in urls:
            try:
                path = f"HasiiMusic/cookies/cookie{random.randint(10000, 99999)}.txt"
                link = url.replace("me/", "me/raw/")
                async with aiohttp.ClientSession() as session:
                    async with session.get(link) as resp:
                        if resp.status != 200:
                            logger.error(f"❌ Cookie download failed: HTTP {resp.status} from {url}")
                            continue
                        content = await resp.read()
                        if not content or len(content) < 50:
                            logger.error(f"❌ Cookie file empty or invalid from {url}")
                            continue
                        with open(path, "wb") as fw:
                            fw.write(content)
                        if os.path.exists(path) and os.path.getsize(path) > 0:
                            saved_count += 1
                            cookie_filename = os.path.basename(path)
                            if cookie_filename not in self.cookies:
                                self.cookies.append(cookie_filename)
                            logger.info(f"✅ Saved: {cookie_filename} ({len(content)} bytes)")
            except Exception as e:
                logger.error(f"❌ Cookie download error from {url}: {e}")

        self.checked = True
        if saved_count > 0:
            logger.info(f"✅ Cookies saved. ({saved_count} file(s))")
        else:
            logger.error("❌ No cookies saved! Check COOKIE_URL in .env.")

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def url(self, message_1: types.Message) -> Union[str, None]:
        messages = [message_1]
        link = None
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)

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
        cache_key = query
        current_time = asyncio.get_running_loop().time()

        if cache_key in self.search_cache:
            cached_result, cache_timestamp = self.search_cache[cache_key]
            if current_time - cache_timestamp < 600:
                fresh = replace(cached_result)
                fresh.message_id = m_id
                fresh.file_path = None
                fresh.user = None
                fresh.time = 0
                fresh.video = False
                return fresh

        try:
            _search = VideosSearch(query, limit=1)
            results = await _search.next()
        except Exception as e:
            logger.warning(f"⚠️ YouTube search failed for '{query}': {e}")
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

            self.search_cache[cache_key] = (track, current_time)
            if len(self.search_cache) > 100:
                oldest_key = min(self.search_cache, key=lambda k: self.search_cache[k][1])
                del self.search_cache[oldest_key]

            return replace(track)
        return None

    async def playlist(self, limit: int, user: str, url: str) -> list[Track]:
        try:
            plist = await Playlist.get(url)
            tracks = []

            if not plist or "videos" not in plist or not plist["videos"]:
                return []

            for data in plist["videos"][:limit]:
                try:
                    thumbnails = data.get("thumbnails", [])
                    thumbnail_url = thumbnails[-1].get("url", "").split("?")[0] if thumbnails else ""
                    link = data.get("link", "")
                    if "&list=" in link:
                        link = link.split("&list=")[0]

                    track = Track(
                        id=data.get("id", ""),
                        channel_name=data.get("channel", {}).get("name", ""),
                        duration=data.get("duration", "0:00"),
                        duration_sec=utils.to_seconds(data.get("duration", "0:00")),
                        title=data.get("title", "Unknown")[:25],
                        thumbnail=thumbnail_url,
                        url=link,
                        user=user,
                        view_count="",
                    )
                    tracks.append(track)
                except Exception:
                    continue

            return tracks
        except KeyError:
            raise Exception("Failed to parse playlist. YouTube may have changed their structure.")
        except Exception:
            raise

    async def download(self, video_id: str, is_live: bool = False, video: bool = False) -> Optional[str]:
        url = self.base + video_id

        # ── Live stream ───────────────────────────────────────────────────────
        if is_live:
            cookie = self.get_cookies()
            ydl_opts: dict = {
                "quiet": True,
                "no_warnings": True,
                "format": "bestaudio/best",
                "noplaylist": True,
                "socket_timeout": 20,
                "extractor_retries": 5,
                "sleep_interval_requests": 1,
                # tv_embedded bypasses bot detection + PO token requirement
                "extractor_args": {"youtube": {"player_client": ["tv_embedded", "ios", "android", "web"]}},
            }
            if cookie:
                ydl_opts["cookiefile"] = cookie

            def _extract_url():
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
                        logger.error("Live stream extraction failed: %s", ex)
                        return None

            try:
                return await asyncio.wait_for(asyncio.to_thread(_extract_url), timeout=35)
            except asyncio.TimeoutError:
                logger.error("Live stream URL extraction timed out for %s", video_id)
                return None

        # ── Audio / Video file download ───────────────────────────────────────
        filename_pattern = f"downloads/{video_id}"
        existing_files = [f for f in glob.glob(f"{filename_pattern}.*") if not f.endswith(".part")]

        if video:
            video_candidates = [f for f in existing_files if Path(f).suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}]
            if video_candidates:
                return video_candidates[0]
        else:
            audio_candidates = [f for f in existing_files if Path(f).suffix.lower() in {".m4a", ".webm", ".opus", ".mp3", ".ogg", ".wav", ".flac"}]
            if audio_candidates:
                return audio_candidates[0]
            container_fallbacks = [f for f in existing_files if Path(f).suffix.lower() in {".mp4", ".mkv", ".mov"}]
            if container_fallbacks:
                return container_fallbacks[0]

        downloads_dir = Path("downloads")
        if not downloads_dir.exists():
            try:
                downloads_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"❌ Cannot create downloads directory: {e}")
                return None

        async with self._download_semaphore:
            cookie = self.get_cookies()
            base_opts: dict = {
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "noplaylist": True,
                "geo_bypass": True,
                "no_warnings": True,
                "overwrites": False,
                "nocheckcertificate": True,
                "continuedl": True,
                "noprogress": True,
                "concurrent_fragment_downloads": 4,
                "http_chunk_size": 524288,
                "socket_timeout": 30,
                "retries": 3,
                "fragment_retries": 3,
                "extractor_retries": 5,
                "sleep_interval_requests": 1,
                # FIX: tv_embedded → no PO token needed, works from datacenter IPs
                # ios → most reliable mobile client, minimal restrictions
                "extractor_args": {"youtube": {"player_client": ["tv_embedded", "ios", "android", "web"]}},
            }

            if video:
                height_filter = f"[height<={self._max_video_height}]" if self._max_video_height else ""
                ydl_opts = {
                    **base_opts,
                    "format": (
                        f"bestvideo[ext=mp4]{height_filter}+bestaudio[ext=m4a]/"
                        f"bestvideo{height_filter}+bestaudio/"
                        "bestvideo+bestaudio/best"
                    ),
                    "merge_output_format": "mp4",
                    "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
                }
            else:
                # FIX: Simple "bestaudio/best" — works for ALL videos
                # Old "bestaudio[ext=m4a]/..." failed when m4a format unavailable
                ydl_opts = {
                    **base_opts,
                    "format": "bestaudio/best",
                    "postprocessors": [],
                }

            if cookie:
                ydl_opts["cookiefile"] = cookie

            def _download(opts):
                ydl_instance = None
                try:
                    ydl_instance = yt_dlp.YoutubeDL(opts)
                    info = ydl_instance.extract_info(url, download=True)
                    if not info:
                        logger.error(f"❌ Failed to extract info for {video_id}")
                        return None
                    time.sleep(0.5)
                    located = self._locate_download_file(video_id, video=video)
                    if located:
                        return located
                    logger.error(f"❌ Download completed but file not found for: {video_id}")
                    return None
                except yt_dlp.utils.ExtractorError as ex:
                    error_msg = str(ex)
                    if "not available" in error_msg.lower():
                        logger.error("❌ Video not available: region-blocked or private.")
                    elif "age" in error_msg.lower():
                        logger.error("❌ Age-restricted video: cookies required.")
                    else:
                        logger.error("❌ YouTube extraction failed: %s", ex)
                    return None
                except yt_dlp.utils.DownloadError as ex:
                    error_msg = str(ex)
                    recovered = self._locate_download_file(video_id, video=video)
                    if "unable to rename file" in error_msg.lower() and recovered:
                        logger.warning(f"⚠️ Renaming failed for {video_id}, using recovered file")
                        return recovered
                    if "416" in error_msg or "Requested range not satisfiable" in error_msg:
                        logger.warning(f"⚠️ Range error for {video_id}, skipping")
                    else:
                        logger.warning(f"⚠️ Download error for {video_id}: {ex}")
                        if recovered:
                            return recovered
                    return None
                except Exception as ex:
                    logger.warning(f"⚠️ Unexpected download error for {video_id}: {ex}")
                    return None
                finally:
                    if ydl_instance:
                        try:
                            ydl_instance.close()
                        except Exception:
                            pass

            return await asyncio.to_thread(_download, ydl_opts)
