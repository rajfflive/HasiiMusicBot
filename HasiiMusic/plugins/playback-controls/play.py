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
    except Exception as e:
        logger.warning(f"Sticker send failed for {chat_id}: {e}")


async def safe_edit(message, text, **kwargs):
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
        return None
    except Exception as e:
        logger.error(f"safe_reply failed: {e}")
        return None


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    return text[:1948] + "</blockquote>"


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
                "Enable with: /channelplay linked</blockquote>"
            )
        try:
            chat = await app.get_chat(channel_id)
            chat_id = channel_id
        except Exception:
            await db.set_cmode(m.chat.id, None)
            return await safe_reply(m,
                "<blockquote>❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ɢᴇᴛ ᴄʜᴀɴɴᴇʟ.</blockquote>"
            )

        client = await db.get_client(channel_id)
        try:
            await app.get_chat_member(channel_id, client.id)
        except Exception:
            try:
                if chat.username:
                    invite_link = chat.username
                else:
                    invite_link = chat.invite_link or await app.export_chat_invite_link(channel_id)
                jm = await safe_reply(m, "<blockquote>🔄 ᴊᴏɪɴɪɴɢ ᴀꜱꜱɪꜱᴛᴀɴᴛ...</blockquote>")
                await client.join_chat(invite_link)
                await asyncio.sleep(1)
                try:
                    await jm.delete()
                except Exception:
                    pass
            except Exception as e:
                return await safe_reply(m,
                    f"<blockquote>❌ ᴄᴏᴜʟᴅ ɴᴏᴛ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ.\n{e}</blockquote>"
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

    if not sent:
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
                    "<blockquote>❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ꜰᴇᴛᴄʜ ᴘʟᴀʏʟɪꜱᴛ.</blockquote>")
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
    for t in tracks:
        t.video = file.video

    if not file.is_live and file.duration_sec > config.DURATION_LIMIT:
        await safe_edit(sent,
            m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60))
        return

    if await db.is_logger():
        await utils.play_log(m, file.title, file.duration)

    file.user = mention

    if force:
        queue.force_add(chat_id, file)
    else:
        position = queue.add(chat_id, file)
        if await db.get_call(chat_id):
            # ── Queued — NO sticker ──────────────────────────────────────────
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
            return  # ← sticker nahi

    if not file.file_path:
        file.file_path = await yt.download(
            file.id,
            is_live=file.is_live,
            video=getattr(file, "video", False),
        )
        if not file.file_path:
            # ── Download fail — NO sticker ───────────────────────────────────
            await safe_edit(sent,
                "<blockquote>❌ ᴅᴏᴡɴʟᴏᴀᴅ ꜰᴀɪʟᴇᴅ.\n\n"
                "• ᴜᴘᴅᴀᴛᴇ ʏᴏᴜᴛᴜʙᴇ ᴄᴏᴏᴋɪᴇꜱ (/ꜱᴇᴛᴄᴏᴏᴋɪᴇꜱ)\n"
                "• ᴠɪᴅᴇᴏ ᴍᴀʏ ʙᴇ ᴘʀɪᴠᴀᴛᴇ ᴏʀ ʀᴇɢɪᴏɴ-ʙʟᴏᴄᴋᴇᴅ</blockquote>")
            return  # ← sticker nahi

    # ── Attempt playback ──────────────────────────────────────────────────────
    play_ok = False
    try:
        await tune.play_media(
            chat_id=chat_id,
            message=sent,
            media=file,
            message_chat_id=message_chat_id if chat_id != message_chat_id else None,
        )
        play_ok = True
    except Exception as e:
        err = str(e)
        if "bot" in err.lower() or "sign in" in err.lower():
            await safe_edit(sent,
                "<blockquote>❌ ʏᴏᴜᴛᴜʙᴇ ʙᴏᴛ ᴅᴇᴛᴇᴄᴛɪᴏɴ.\n\n"
                "ᴜᴘᴅᴀᴛᴇ ᴄᴏᴏᴋɪᴇꜱ ᴡɪᴛʜ /ꜱᴇᴛᴄᴏᴏᴋɪᴇꜱ ᴀɴᴅ ʀᴇᴛʀʏ.</blockquote>")
        else:
            await safe_edit(sent,
                f"<blockquote>❌ ᴘʟᴀʏʙᴀᴄᴋ ᴇʀʀᴏʀ:\n{err}</blockquote>")
        return

    # ── Play succeeded → send sticker ────────────────────────────────────────
    if play_ok:
        await send_random_sticker(m.chat.id)

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
