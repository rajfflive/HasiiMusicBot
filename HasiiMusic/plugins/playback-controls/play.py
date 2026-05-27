import asyncio
import logging
import random

from pyrogram import filters, types
from pyrogram.errors import (
    ChatSendPlainForbidden,
    ChatWriteForbidden,
    FloodWait,
    MessageDeleteForbidden,
    MessageIdInvalid,
)

from HasiiMusic import app, config, db, lang, queue, tg, tune, yt
from HasiiMusic.helpers import buttons, utils
from HasiiMusic.helpers._play import checkUB

logger = logging.getLogger(__name__)


PLAY_STICKERS = [
    "CAACAgUAAxkBAAFK0EBqF2Hz5XIE7xHiEXymgH80LfpcvgAC-x4AAmuHwVQuNt2y6iv3tTsE",
    "CAACAgUAAxkBAAFK0EFqF2Hzep2LEv4IgHLGdhJ-kHNncQACxhwAAjqiuVScgTvFrqU3OjsE",
    "CAACAgUAAxkBAAFK0EJqF2HzVULsHMM6CmOUy3mZFYtuJAAC9SIAAujBwFQBHAjKr4hsUjsE",
    "CAACAgUAAxkBAAFK0ENqF2H06DbUedXZT5zqDIjCq5nxOAAClyMAApCJuVQUFrZzrk7S7DsE",
]


async def send_random_sticker(chat_id: int) -> None:
    try:
        await app.send_sticker(chat_id, random.choice(PLAY_STICKERS))
    except Exception:
        pass


async def safe_edit(message, text, **kwargs):
    try:
        await message.edit_text(text, **kwargs)
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            await message.edit_text(text, **kwargs)
            return True
        except (MessageIdInvalid, MessageDeleteForbidden, Exception):
            return False
    except (MessageIdInvalid, MessageDeleteForbidden):
        return False
    except Exception:
        return False


async def safe_reply(message, text, **kwargs):
    try:
        return await message.reply_text(text, **kwargs)
    except (ChatSendPlainForbidden, ChatWriteForbidden):
        logger.warning(f"Cannot send text in chat {message.chat.id}")
        return None
    except Exception as e:
        logger.error(f"Failed to send reply: {e}")
        return None


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text


@app.on_message(
    filters.command(
        ["play", "playforce", "cplay", "cplayforce",
         "vplay", "vplayforce", "cvplay", "cvplayforce"]
    )
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    url: str = None,
    cplay: bool = False,
    video: bool = False,
) -> None:
    try:
        await m.delete()
    except Exception:
        pass

    chat_id = m.chat.id
    message_chat_id = m.chat.id

    if cplay:
        channel_id = await db.get_cmode(m.chat.id)
        if channel_id is None:
            return await safe_reply(m,
                "<blockquote>❌ Channel play is not enabled.\n\n"
                "To enable for linked channel:\n"
                "`/channelplay linked`\n\n"
                "To enable for any channel:\n"
                "`/channelplay [channel_id]`</blockquote>"
            )
        try:
            chat = await app.get_chat(channel_id)
            chat_id = channel_id
        except Exception:
            await db.set_cmode(m.chat.id, None)
            return await safe_reply(m,
                "<blockquote>❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ɢᴇᴛ ᴄʜᴀɴɴᴇʟ.\n\n"
                "ᴍᴀᴋᴇ ꜱᴜʀᴇ ɪ'ᴍ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴄʜᴀɴɴᴇʟ ᴘʟᴀʏ ɪꜱ ꜱᴇᴛ ᴄᴏʀʀᴇᴄᴛʟʏ.</blockquote>"
            )

        client = await db.get_client(channel_id)
        try:
            await app.get_chat_member(channel_id, client.id)
        except Exception:
            try:
                if chat.username:
                    invite_link = chat.username
                else:
                    try:
                        invite_link = chat.invite_link
                        if not invite_link:
                            invite_link = await app.export_chat_invite_link(channel_id)
                    except Exception:
                        return await safe_reply(m,
                            f"<blockquote>❌ ᴀꜱꜱɪꜱᴛᴀɴᴛ ɴᴏᴛ ɪɴ ᴄʜᴀɴɴᴇʟ!\n\n"
                            f"ᴘʟᴇᴀꜱᴇ ᴀᴅᴅ @{client.username if client.username else client.mention} "
                            f"ᴛᴏ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴀꜱ ᴀᴅᴍɪɴ ᴡɪᴛʜ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ.</blockquote>"
                        )
                join_msg = await safe_reply(m, "<blockquote>🔄 ᴊᴏɪɴɪɴɢ ᴀꜱꜱɪꜱᴛᴀɴᴛ ᴛᴏ ᴄʜᴀɴɴᴇʟ...</blockquote>")
                await client.join_chat(invite_link)
                await asyncio.sleep(1)
                try:
                    await join_msg.delete()
                except Exception:
                    pass
            except Exception as e:
                return await safe_reply(m,
                    f"<blockquote>❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴊᴏɪɴ ᴀꜱꜱɪꜱᴛᴀɴᴛ ᴛᴏ ᴄʜᴀɴɴᴇʟ!\n\n"
                    f"ᴘʟᴇᴀꜱᴇ ᴍᴀɴᴜᴀʟʟʏ ᴀᴅᴅ @{client.username if client.username else client.mention} "
                    f"ᴛᴏ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴀꜱ ᴀᴅᴍɪɴ ᴡɪᴛʜ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ.\n\n"
                    f"Error: {str(e)}</blockquote>"
                )

    play_emoji = m.lang["play_emoji"]
    try:
        sent = await safe_reply(m, m.lang["play_searching"].format(play_emoji))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            sent = await safe_reply(m, m.lang["play_searching"].format(play_emoji))
        except FloodWait as e2:
            await asyncio.sleep(e2.value)
            return
        except Exception:
            return
    except Exception:
        return

    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []
    file = None

    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)
    elif url:
        if "playlist" in url:
            await safe_edit(sent, m.lang["playlist_fetch"])
            try:
                tracks = await yt.playlist(config.PLAYLIST_LIMIT, mention, url)
            except Exception:
                await safe_edit(
                    sent,
                    "<blockquote>❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ꜰᴇᴛᴄʜ ᴘʟᴀʏʟɪꜱᴛ.\n\n"
                    "ʏᴏᴜᴛᴜʙᴇ ᴘʟᴀʏʟɪꜱᴛꜱ ᴀʀᴇ ᴄᴜʀʀᴇɴᴛʟʏ ᴇxᴘᴇʀɪᴇɴᴄɪɴɢ ɪꜱꜱᴜᴇꜱ. "
                    "ᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴘʟᴀʏɪɴɢ ɪɴᴅɪᴠɪᴅᴜᴀʟ ꜱᴏɴɢꜱ ɪɴꜱᴛᴇᴀᴅ.</blockquote>",
                )
                return
            if not tracks:
                await safe_edit(sent, m.lang["playlist_error"])
                return
            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            file = await yt.search(url, sent.id)
        if not file:
            await safe_edit(sent, m.lang["play_not_found"].format(config.SUPPORT_CHAT))
            return
    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        file = await yt.search(query, sent.id)
        if not file:
            await safe_edit(sent, m.lang["play_not_found"].format(config.SUPPORT_CHAT))
            return

    if not file:
        return

    file.video = getattr(file, "video", False) or video
    if file.video:
        for track in tracks:
            track.video = True

    if not file.is_live and file.duration_sec > config.DURATION_LIMIT:
        await safe_edit(sent, m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60))
        return

    if await db.is_logger():
        await utils.play_log(m, file.title, file.duration)

    file.user = mention
    if force:
        queue.force_add(chat_id, file)
    else:
        position = queue.add(chat_id, file)
        if await db.get_call(chat_id):
            # Queued — NO sticker
            await safe_edit(
                sent,
                m.lang["play_queued"].format(
                    position, file.url, file.title, file.duration, m.from_user.mention,
                ),
                reply_markup=buttons.play_queued(chat_id, file.id, m.lang["play_now"]),
            )
            if tracks:
                added = playlist_to_queue(chat_id, tracks)
                try:
                    await app.send_message(
                        chat_id=m.chat.id,
                        text=m.lang["playlist_queued"].format(len(tracks)) + added,
                    )
                except Exception:
                    pass
            try:
                from HasiiMusic import preload
                asyncio.create_task(preload.start_preload(chat_id, count=2))
            except Exception:
                pass
            return  # ← sticker nahi aayega queue pe

    if not file.file_path:
        file.file_path = await yt.download(
            file.id,
            is_live=file.is_live,
            video=getattr(file, "video", False),
        )
        if not file.file_path:
            # Download failed — NO sticker
            await safe_edit(
                sent,
                "<blockquote>❌ Failed to download media.\n\n"
                "Possible reasons:\n"
                "• YouTube detected bot activity (update cookies)\n"
                "• Video is region-blocked or private\n"
                "• Age-restricted content (requires cookies)</blockquote>",
            )
            return  # ← sticker nahi aayega download fail pe

    try:
        await tune.play_media(
            chat_id=chat_id,
            message=sent,
            media=file,
            message_chat_id=message_chat_id if chat_id != message_chat_id else None,
        )
        # ✅ Sirf yahan aayega sticker — actual play start hua
        await send_random_sticker(m.chat.id)

    except Exception as e:
        # Play failed — NO sticker
        error_msg = str(e)
        if "bot" in error_msg.lower() or "sign in" in error_msg.lower():
            await safe_edit(
                sent,
                "<blockquote>❌ YouTube bot detection triggered.\n\n"
                "Solution:\n"
                "• Update YouTube cookies in `HasiiMusic/cookies/` folder\n"
                "• Wait a few minutes before trying again\n"
                "• Try /radio for uninterrupted music\n\n"
                f"Support: {config.SUPPORT_CHAT}</blockquote>",
            )
        else:
            await safe_edit(
                sent,
                f"<blockquote>❌ Playback error:\n{error_msg}\n\n"
                f"Support: {config.SUPPORT_CHAT}</blockquote>",
            )
        return

    if not tracks:
        return

    added = playlist_to_queue(chat_id, tracks)
    try:
        await app.send_message(
            chat_id=m.chat.id,
            text=m.lang["playlist_queued"].format(len(tracks)) + added,
        )
    except Exception:
        pass
