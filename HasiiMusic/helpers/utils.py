from pyrogram.types import Message

async def send_log(message: Message):
    try:
        from HasiiMusic import app, config
        if config.LOGGER_ID:
            text = f"#NEW_USER\nID: `{message.from_user.id}`\nName: {message.from_user.mention}"
            await app.send_message(config.LOGGER_ID, text)
    except Exception:
        pass

async def safe_text(message: Message, text: str, reply_markup=None, quote=True):
    try:
        await message.reply_text(text, reply_markup=reply_markup, quote=quote, parse_mode="html")
    except Exception:
        await message.reply_text(text, quote=quote)
