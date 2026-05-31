"""
play.py — v3 with GIF Manager (Bot se seedha GIF change karo!)

/play, /playforce, /cplay, /vplay etc. — same as before

Play GIF Management (owner/sudo only — private ya group mein):
  /setplaygif      - Reply to GIF/sticker → add to play list
  /setplaygif naam - Reply + custom name
  /rmplaygif <n>   - Remove by number
  /listplaygif     - See all play GIFs/stickers

Ab hardcoded sticker IDs ki jagah MongoDB se GIF/sticker aayega!
"""

from pyrogram import filters, types
from pyrogram.errors import (
    FloodWait, MessageIdInvalid, MessageDeleteForbidden,
    ChatSendPlainForbidden, ChatWriteForbidden,
)

from HasiiMusic import tune, app, config, db, lang, queue, tg, yt
from HasiiMusic.helpers import buttons, utils
from HasiiMusic.helpers._play import checkUB
from HasiiMusic.helpers.gif_manager import (
    get_random_gif,
    register_gif_commands,
    get_gifs,
    add_gif,
    remove_gif,
    list_gifs_text,
    is_owner_or_sudo,
    extract_file_id,
)
import asyncio
import logging
import random

logger = logging.getLogger(__name__)

# ─── Register /setplaygif, /rmplaygif, /listplaygif ──────────────────────────
# Note: play GIF sirf owner/sudo set kar sakta hai (private ya group dono mein)
register_gif_commands(app, "play", "play")


async def send_play_gif(chat_id: int) -> None:
    """Send a random play GIF/sticker. Falls back to hardcoded stickers."""
    gif = get_random_gif("play")
    if not gif:
        return

    # Try as sticker first (for sticker file_ids)
    try:
        await app.send_sticker(chat_id, gif)
        return
    except Exception:
        pass

    # Try as animation/GIF
    try:
        await app.send_animation(chat_id, gif)
        return
    except Exception:
        pass


async def safe_edit(message, text, **kwargs) -> bool:
    try:
        await message.edit_text(text, **kwargs)
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            await message.edit_text(text, **kwargs)
            return True
        except Exception:
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
    return text[:1948] + "</blockquote>"


@app.on_message(
    filters.command([
        "play", "playforce",
        "cplay", "cplayforce",
        "vplay", "vplayforce",
        "cvplay", "cvplayforce",
    ])
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

    # ── Play GIF — processing indicator ──────────────────────────────────────
    await send_play_gif(m.chat.id)

    chat_id = m.chat.id
    message_chat_id = m.chat.id

    if cplay:
        channel_id = await db.get_cmode(m.chat.id)
        if channel_id is None:
            return await safe_reply(m,
                "<blockquote>❌ Channel play is not enabled.\n\n"
                "To enable for linked channel: <code>/channelplay linked</code>\n"
                "To enable for any channel: <code>/channelplay [channel_id]</code></blockquote>"
            )
        try:
            chat = await app.get_chat(channel_id)
            chat_id = channel_id
        except Exception:
            await db.set_cmode(m.chat.id, None)
            return await safe_reply(m,
                "<blockquote>❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ɢᴇᴛ ᴄʜᴀɴɴᴇʟ.\n\n"
                "ᴍᴀᴋᴇ ꜱᴜʀᴇ ɪ'ᴍ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ.</blockquote>"
            )

        client = await db.get_client(channel_id)
        try:
            await app.get_chat_member(channel_id, client.id)
        except Exception:
            try:
                if chat.username:
                    invite_link = chat.username
                else:
                    invite_link = chat.invite_link
                    if not invite_link:
                        invite_link = await app.export_chat_invite_link(channel_id)

                join_msg = await safe_reply(m,
                    "<blockquote>🔄 ᴊᴏɪɴɪɴɢ ᴀꜱꜱɪꜱᴛᴀɴᴛ ᴛᴏ ᴄʜᴀɴɴᴇʟ...</blockquote>"
                )
                await client.join_chat(invite_link)
                await asyncio.sleep(1)
                try:
                    await join_msg.delete()
                except Exception:
                    pass

            except Exception as e:
                return await safe_reply(m,
                    f"<blockquote>❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴊᴏɪɴ ᴀꜱꜱɪꜱᴛᴀɴᴛ ᴛᴏ ᴄʜᴀɴɴᴇʟ!\n\n"
                    f"ᴘʟᴇᴀꜱᴇ ᴀᴅᴅ @{client.username or client.mention} ᴀꜱ ᴀᴅᴍɪɴ.\n\n"
                    f"Error: {e}</blockquote>"
                )

    play_emoji = m.lang["play_emoji"]

    try:
        sent = await safe_reply(m, m.lang["play_searching"].format(play_emoji))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            sent = await safe_reply(m, m.lang["play_searching"].format(play_emoji))
        except Exception:
            return
    except Exception:
        return

    if sent is None:
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
                await safe_edit(sent,
                    "<blockquote>❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ꜰᴇᴛᴄʜ ᴘʟᴀʏʟɪꜱᴛ.\n"
                    "ᴘʟᴇᴀꜱᴇ ᴛʀʏ ɪɴᴅɪᴠɪᴅᴜᴀʟ ꜱᴏɴɢꜱ.</blockquote>"
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
            await safe_edit(
                sent,
                m.lang["play_queued"].format(
                    position, file.url, file.title,
                    file.duration, m.from_user.mention,
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

            return

    if not file.file_path:
        file.file_path = await yt.download(
            file.id,
            is_live=file.is_live,
            video=getattr(file, "video", False),
        )
        if not file.file_path:
            await safe_edit(sent, m.lang["error_no_file"].format(config.SUPPORT_CHAT))
            return

    try:
        await tune.play_media(
            chat_id=chat_id,
            message=sent,
            media=file,
            message_chat_id=message_chat_id if chat_id != message_chat_id else None,
        )
    except Exception as e:
        logger.error(f"[Play] play_media failed: {e}")
        await safe_edit(sent, m.lang["error_no_file"].format(config.SUPPORT_CHAT))
        return

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
