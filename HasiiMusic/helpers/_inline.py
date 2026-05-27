from pyrogram import types as ptypes
from HasiiMusic import app, config


class SBtn:
    """
    Styled button wrapper for Pyrogram.
    style: 'primary' | 'success' | 'danger' | 'warning'
    """
    def __init__(self, text, style=None, callback_data=None, url=None, copy_text=None):
        self.text = text
        self.style = style
        self.callback_data = callback_data
        self.url = url
        self.copy_text = copy_text

    def build(self) -> ptypes.InlineKeyboardButton:
        kwargs = {"text": self.text}
        if self.callback_data:
            kwargs["callback_data"] = self.callback_data
        if self.url:
            kwargs["url"] = self.url
        if self.copy_text:
            kwargs["copy_text"] = self.copy_text
        return ptypes.InlineKeyboardButton(**kwargs)


def _b(text, style=None, **kw) -> ptypes.InlineKeyboardButton:
    return SBtn(text, style=style, **kw).build()


class Inline:
    def __init__(self):
        self.ikm = ptypes.InlineKeyboardMarkup

    def cancel_dl(self, text) -> ptypes.InlineKeyboardMarkup:
        return self.ikm([[_b(text, style="danger", callback_data="cancel_dl")]])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> ptypes.InlineKeyboardMarkup:
        keyboard = []
        if status:
            keyboard.append([_b(status, style="primary",
                                callback_data=f"controls status {chat_id}")])
        elif timer:
            keyboard.append([_b(timer, style="primary",
                                callback_data=f"controls status {chat_id}")])
        if not remove:
            keyboard.append([
                _b("« 30",  callback_data=f"controls seek_back_30 {chat_id}"),
                _b("« 10",  callback_data=f"controls seek_back_10 {chat_id}"),
                _b("10 »",  callback_data=f"controls seek_forward_10 {chat_id}"),
                _b("30 »",  callback_data=f"controls seek_forward_30 {chat_id}"),
            ])
            keyboard.append([
                _b("▷",   style="success", callback_data=f"controls resume {chat_id}"),
                _b("II",  style="primary", callback_data=f"controls pause {chat_id}"),
                _b("↻",   style="primary", callback_data=f"controls replay {chat_id}"),
                _b("‣‣I", style="primary", callback_data=f"controls skip {chat_id}"),
                _b("▢",   style="danger",  callback_data=f"controls stop {chat_id}"),
            ])
            keyboard.append([
                _b("ᴅᴇʟᴇᴛᴇ", style="danger",
                   callback_data=f"controls close {chat_id}")
            ])
        return self.ikm(keyboard)

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> ptypes.InlineKeyboardMarkup:
        if back:
            rows = [[_b("ʙᴀᴄᴋ", style="primary", callback_data="help_main")]]
        else:
            rows = [
                [
                    _b("ᴀᴅᴍɪɴꜱ",    style="primary", callback_data="help_admins"),
                    _b("ᴀᴜᴛʜ",      style="primary", callback_data="help_auth"),
                    _b("ʙʀᴏᴀᴅᴄᴀꜱᴛ", style="primary", callback_data="help_broadcast"),
                ],
                [
                    _b("ʙʟ-ᴄʜᴀᴛ", style="danger", callback_data="help_blchat"),
                    _b("ʙʟ-ᴜꜱᴇʀ", style="danger", callback_data="help_bluser"),
                    _b("ɢ-ʙᴀɴ",   style="danger", callback_data="help_gban"),
                ],
                [
                    _b("ʟᴏᴏᴘ",   style="success", callback_data="help_loop"),
                    _b("ᴘʟᴀʏ",   style="success", callback_data="help_play"),
                    _b("ǫᴜᴇᴜᴇ", style="success", callback_data="help_queue"),
                ],
                [
                    _b("ꜱᴇᴇᴋ",    style="primary", callback_data="help_seek"),
                    _b("ꜱʜᴜꜰꜰʟᴇ", style="primary", callback_data="help_shuffle"),
                    _b("ᴘɪɴɢ",   style="primary", callback_data="help_ping"),
                ],
                [
                    _b("ꜱᴛᴀᴛꜱ",      style="primary", callback_data="help_stats"),
                    _b("ꜱᴜᴅᴏ",       style="danger",  callback_data="help_sudo"),
                    _b("ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ", style="danger",  callback_data="help_maintenance"),
                ],
                [_b("ʙᴀᴄᴋ", style="primary", callback_data="start")],
            ]
        return self.ikm(rows)

    def ping_markup(self, text: str) -> ptypes.InlineKeyboardMarkup:
        return self.ikm([
            [
                _b("📢 Channel", style="primary", url=config.SUPPORT_CHANNEL),
                _b("🍂 Support", style="success", url=config.SUPPORT_CHAT),
            ],
            [
                _b("➕ Add Me to Your Group", style="success",
                   url=f"https://t.me/{app.username}?startgroup=true"),
            ],
        ])

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> ptypes.InlineKeyboardMarkup:
        return self.ikm([
            [
                _b("▷",   style="success", callback_data=f"controls resume {chat_id}"),
                _b("∣ ∣", style="primary", callback_data=f"controls pause {chat_id}"),
                _b(">>",  style="primary", callback_data=f"controls skip {chat_id}"),
                _b("▣",   style="danger",  callback_data=f"controls stop {chat_id}"),
            ],
            [_b("ᴅᴇʟᴇᴛᴇ", style="danger",
                callback_data=f"controls close {chat_id}")],
        ])

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> ptypes.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        _style  = "primary" if playing else "success"
        return self.ikm([[
            _b(_text, style=_style,
               callback_data=f"controls {_action} {chat_id} q")
        ]])

    def settings_markup(
        self, lang: dict, admin_only: bool, language: str, chat_id: int
    ) -> ptypes.InlineKeyboardMarkup:
        return self.ikm([[
            _b(lang["play_mode"] + " ➜", style="primary",
               callback_data=f"controls status {chat_id}"),
            _b(admin_only, style="success", callback_data="playmode"),
        ]])

    def start_key(
        self, lang: dict, private: bool = False
    ) -> ptypes.InlineKeyboardMarkup:
        return self.ikm([
            [_b(lang["add_me"], style="success",
                url=f"https://t.me/{app.username}?startgroup=true")],
            [_b(lang["help"], style="primary", callback_data="help")],
            [
                _b(lang["support"], style="danger",  url=config.SUPPORT_CHAT),
                _b(lang["channel"], style="success", url=config.SUPPORT_CHANNEL),
            ],
        ])

    def yt_key(self, link: str) -> ptypes.InlineKeyboardMarkup:
        return self.ikm([[
            _b("ᴄᴏᴘʏ ʟɪɴᴋ",        style="primary", copy_text=link),
            _b("ᴏᴘᴇɴ ɪɴ ʏᴏᴜᴛᴜʙᴇ", style="success", url=link),
        ]])
