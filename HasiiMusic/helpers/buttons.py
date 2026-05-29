from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def start_key(lang_dict, private=True):
    keyboard = []
    if private:
        keyboard.append([InlineKeyboardButton("📚 Help", callback_data="help"),
                         InlineKeyboardButton("⚙️ Settings", callback_data="settings")])
        keyboard.append([InlineKeyboardButton("➕ Add to Group", url="https://t.me/share/url?url=...")])
    else:
        keyboard.append([InlineKeyboardButton("📚 Help", callback_data="help")])
    return InlineKeyboardMarkup(keyboard)

def help_markup(lang_dict):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Home", callback_data="start"),
         InlineKeyboardButton("❌ Close", callback_data="close")]
    ])

def settings_markup(lang_dict, admin_only, lang_code, chat_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔊 Audio Quality", callback_data="set_audio")],
        [InlineKeyboardButton("🗣 Language", callback_data="set_lang")],
        [InlineKeyboardButton("🔙 Back", callback_data="start")]
    ])

def ping_markup(support_url):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Support", url=support_url),
         InlineKeyboardButton("🏠 Home", callback_data="start")]
    ])
