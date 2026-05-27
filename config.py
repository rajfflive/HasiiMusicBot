from os import getenv
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):

        # ── TELEGRAM API ──────────────────────────────────────────────
        self.API_ID: int = int(getenv("API_ID", "0"))
        self.API_HASH: str = getenv("API_HASH", "")

        # ── BOT CONFIG ────────────────────────────────────────────────
        self.BOT_TOKEN: str = getenv("BOT_TOKEN", "")
        self.LOGGER_ID: int = int(getenv("LOGGER_ID", "0"))
        self.OWNER_ID: int = int(getenv("OWNER_ID", "0"))

        # ── DATABASE ──────────────────────────────────────────────────
        self.MONGO_URL: str = getenv("MONGO_DB_URI", "")

        # ── MUSIC LIMITS ──────────────────────────────────────────────
        self.DURATION_LIMIT: int = int(getenv("DURATION_LIMIT", "300")) * 60
        self.QUEUE_LIMIT: int = int(getenv("QUEUE_LIMIT", "30"))
        self.PLAYLIST_LIMIT: int = int(getenv("PLAYLIST_LIMIT", "20"))

        # ── ASSISTANT SESSIONS ────────────────────────────────────────
        self.SESSION1: str = getenv("STRING_SESSION", "")
        self.SESSION2: str = getenv("STRING_SESSION2", "")
        self.SESSION3: str = getenv("STRING_SESSION3", "")

        # ── SUPPORT LINKS ─────────────────────────────────────────────
        self.SUPPORT_CHANNEL: str = getenv("SUPPORT_CHANNEL", "https://t.me/hasiimusic")
        self.SUPPORT_CHAT: str = getenv("SUPPORT_CHAT", "https://t.me/TheInfinityAI")

        # ── EXCLUDED CHATS ────────────────────────────────────────────
        self.EXCLUDED_CHATS: List[int] = self._parse_excluded_chats()

        # ── FEATURE FLAGS ─────────────────────────────────────────────
        self.AUTO_END: bool = self._str_to_bool(getenv("AUTO_END", "False"))
        self.AUTO_LEAVE: bool = self._str_to_bool(getenv("AUTO_LEAVE", "False"))
        self.THUMB_GEN: bool = self._str_to_bool(getenv("THUMB_GEN", "True"))
        self.VIDEO_PLAY: bool = self._str_to_bool(getenv("VIDEO_PLAY", "False"))
        self.VIDEO_MAX_HEIGHT: int = self._parse_video_height()

        # ── YOUTUBE COOKIES ───────────────────────────────────────────
        self.COOKIES_URL: List[str] = self._parse_cookies()

        # ── IMAGES ───────────────────────────────────────────────────
        self.DEFAULT_THUMB: str = getenv("DEFAULT_THUMB", "https://files.catbox.moe/kgrs8f.png")
        self.PING_IMG: str = getenv("PING_IMG", "https://files.catbox.moe/djilyq.png")
        self.START_IMG: str = getenv("START_IMG", "https://files.catbox.moe/7jihmf.png")
        self.RADIO_IMG: str = getenv("RADIO_IMG", "https://files.catbox.moe/t03fzk.png")

        # ── MODERATION ────────────────────────────────────────────────
        self.EXCLUDED_USERNAMES: List[str] = getenv("EXCLUDED_USERNAMES", "").split()

    # ── Parsers ───────────────────────────────────────────────────────────────

    def _parse_video_height(self) -> int:
        raw = getenv("VIDEO_MAX_HEIGHT", "1080")
        try:
            h = int(raw)
        except (TypeError, ValueError):
            return 1080
        if h <= 0:
            return 0
        return max(480, min(h, 2160))

    def _parse_excluded_chats(self) -> List[int]:
        excluded = getenv("EXCLUDED_CHATS", "")
        if not excluded:
            return []
        result = []
        for chat_id in excluded.split(","):
            chat_id = chat_id.strip()
            if chat_id.lstrip("-").isdigit():
                result.append(int(chat_id))
        return result

    def _parse_cookies(self) -> List[str]:
        """
        Parse YouTube cookie URLs from COOKIE_URL env var.
        Multiple URLs supported — space separated.
        Accepts any valid http/https URL.
        """
        cookie_str = getenv("COOKIE_URL", "")
        if not cookie_str:
            return []
        return [
            url.strip()
            for url in cookie_str.split()
            if url.strip() and url.strip().startswith("http")
        ]

    @staticmethod
    def _str_to_bool(value: str) -> bool:
        return value.lower() in ("true", "1", "yes", "y", "on")

    # ── Validation ────────────────────────────────────────────────────────────

    def check(self) -> None:
        required = {
            "API_ID": self.API_ID,
            "API_HASH": self.API_HASH,
            "BOT_TOKEN": self.BOT_TOKEN,
            "MONGO_DB_URI": self.MONGO_URL,
            "LOGGER_ID": self.LOGGER_ID,
            "OWNER_ID": self.OWNER_ID,
            "STRING_SESSION": self.SESSION1,
        }
        missing = [
            name for name, value in required.items()
            if not value or (isinstance(value, int) and value == 0)
        ]
        if missing:
            raise SystemExit(
                f"❌ Missing env variables: {', '.join(missing)}\n"
                f"Please set them in Render environment variables."
            )


config = Config()
