# ==============================================================================
# config.py - Bot Configuration Manager
# ==============================================================================
# This file loads all configuration settings from environment variables (.env file).
#
# What it does:
# - Reads settings from .env file (API keys, bot token, database URL, etc.)
# - Validates that all required settings are present
# - Provides default values for optional settings
# - Converts string values to appropriate types (int, bool, list)
#
# Important: Never commit your .env file to git! It contains sensitive data.
# Use sample.env as a template to create your own .env file.
# ==============================================================================

"""
Configuration module for ˹ʜᴀꜱɪɪ ᴍᴜꜱɪᴄ˼.

This module loads and validates all environment variables required for the bot to function.
It provides a centralized Config class that manages all configuration settings.
"""

from os import getenv
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file (create one from sample.env)
load_dotenv()


class Config:
    """
    Configuration class for managing bot settings.

    All settings are loaded from environment variables with sensible defaults where applicable.
    Required variables are validated on initialization through the check() method.
    """

    def __init__(self):
        """Initialize configuration by loading all environment variables."""

        # ============ TELEGRAM API CREDENTIALS ============
        self.API_ID: int = int(getenv("API_ID", "0"))
        self.API_HASH: str = getenv("API_HASH", "")

        # ============ BOT CONFIGURATION ============
        self.BOT_TOKEN: str = getenv("BOT_TOKEN", "")
        self.LOGGER_ID: int = int(getenv("LOGGER_ID", "0"))
        self.OWNER_ID: int = int(getenv("OWNER_ID", "7981894574"))

        # ============ DATABASE CONFIGURATION ============
        self.MONGO_URL: str = getenv("MONGO_DB_URI", "")

        # ============ MUSIC BOT LIMITS ============
        self.DURATION_LIMIT: int = int(getenv("DURATION_LIMIT", "300")) * 60
        self.QUEUE_LIMIT: int = int(getenv("QUEUE_LIMIT", "30"))
        self.PLAYLIST_LIMIT: int = int(getenv("PLAYLIST_LIMIT", "20"))

        # ============ ASSISTANT/USERBOT SESSIONS ============
        self.SESSION1: str = getenv("STRING_SESSION", "")
        self.SESSION2: str = getenv("STRING_SESSION2", "")
        self.SESSION3: str = getenv("STRING_SESSION3", "")

        # ============ SUPPORT LINKS ============
        self.SUPPORT_CHANNEL: str = getenv(
            "SUPPORT_CHANNEL", "https://t.me/hasiimusic")
        self.SUPPORT_CHAT: str = getenv("SUPPORT_CHAT", "https://t.me/TheInfinityAI")

        # ============ EXCLUDED CHATS ============
        self.EXCLUDED_CHATS: List[int] = self._parse_excluded_chats()

        # ============ FEATURE FLAGS ============
        self.AUTO_END: bool = self._str_to_bool(getenv("AUTO_END", "False"))
        self.AUTO_LEAVE: bool = self._str_to_bool(getenv("AUTO_LEAVE", "False"))
        self.THUMB_GEN: bool = self._str_to_bool(getenv("THUMB_GEN", "True"))
        self.VIDEO_PLAY: bool = self._str_to_bool(getenv("VIDEO_PLAY", "False"))
        self.VIDEO_MAX_HEIGHT: int = self._parse_video_height()

        # ============ YOUTUBE COOKIES ============
        self.COOKIES_URL: List[str] = self._parse_cookies()

        # ============ IMAGE URLS ============
        self.DEFAULT_THUMB: str = getenv(
            "DEFAULT_THUMB",
            "https://files.catbox.moe/kgrs8f.png"
        )
        self.PING_IMG: str = getenv(
            "PING_IMG", "https://files.catbox.moe/djilyq.png")
        self.START_IMG: str = getenv(
            "START_IMG", "https://files.catbox.moe/7jihmf.png")
        self.RADIO_IMG: str = getenv(
            "RADIO_IMG", "https://files.catbox.moe/t03fzk.png")

        # ============ MODERATION ============
        self.EXCLUDED_USERNAMES: List[str] = getenv("EXCLUDED_USERNAMES", "").split()

    def _parse_video_height(self) -> int:
        """Clamp configured video height to a safe HD range."""
        default_height = 1080
        raw_value = getenv("VIDEO_MAX_HEIGHT", str(default_height))
        try:
            height = int(raw_value)
        except (TypeError, ValueError):
            return default_height
        if height <= 0:
            return 0
        return max(480, min(height, 2160))

    def _parse_excluded_chats(self) -> List[int]:
        """Parse excluded chat IDs from comma-separated string."""
        excluded = getenv("EXCLUDED_CHATS", "")
        if not excluded:
            return []
        chat_ids = []
        for chat_id in excluded.split(","):
            chat_id = chat_id.strip()
            if chat_id.lstrip('-').isdigit():
                chat_ids.append(int(chat_id))
        return chat_ids

    def _parse_cookies(self) -> List[str]:
        """
        Parse YouTube cookie URLs from space-separated string.
        Accepts any valid HTTP/HTTPS URL — no site restriction.
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
        """Convert string to boolean value."""
        return value.lower() in ("true", "1", "yes", "y", "on")

    def check(self) -> None:
        """Validate that all required environment variables are set."""
        required_vars = {
            "API_ID": self.API_ID,
            "API_HASH": self.API_HASH,
            "BOT_TOKEN": self.BOT_TOKEN,
            "MONGO_DB_URI": self.MONGO_URL,
            "LOGGER_ID": self.LOGGER_ID,
            "OWNER_ID": self.OWNER_ID,
            "STRING_SESSION": self.SESSION1,
        }

        missing = [
            name for name, value in required_vars.items()
            if not value or (isinstance(value, int) and value == 0)
        ]

        if missing:
            raise SystemExit(
                f"❌ Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file and ensure all required variables are set."
            )
