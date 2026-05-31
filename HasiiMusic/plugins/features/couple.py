"""
Couple Plugin — v5 FINAL (All English)
Place at: HasiiMusic/plugins/features/couple.py

Commands:
  /couple @user   - Ship yourself with someone
  /uncouple       - Break up
  /mycouple       - Check your couple status
  /couples        - Random couple from group members
  /couplerank     - Top couples leaderboard

GIF Management:
  /setcouplegif, /rmcouplegif <n>, /listcouplegif
"""

import random
import time
from datetime import timedelta

from pyrogram import enums, filters
from pyrogram.types import Message
from pymongo import MongoClient as PyMongoClient

from HasiiMusic.helpers.gif_manager import get_random_gif, register_gif_commands
from HasiiMusic import app

try:
    from HasiiMusic.core.mongo import mongodb as _db
except Exception:
    import os
    _c = PyMongoClient(os.getenv("MONGO_DB_URI", "mongodb://localhost:27017"))
    _db = _c["HasiiMusicBot"]

couples_col = _db["couples"]

COUPLE_LINES = [
    "Two souls, one heartbeat — you were made for each other 💞",
    "Every love story is beautiful, but yours is my favorite ✨",
    "In a world full of people, you found each other — that's magic 🌟",
    "Love isn't about perfection, it's about choosing each other every day 💑",
    "You're the reason I believe in love at first sight 💘",
    "Together you're unstoppable — the ultimate duo 🔥",
    "When two hearts align, the universe takes notice 🌌",
    "The best kind of love is the unexpected kind 🎯",
    "You complete each other in ways words can't describe 💫",
    "Love found you before you even knew to look 🌺",
    "This ship just sailed — and it's sailing straight to paradise 🚢",
    "Chemistry, connection, and a little bit of destiny 💖",
    "Side by side, or miles apart — real love bridges every gap 🌉",
    "They say love is blind, but you two can clearly see each other's soul 👁️‍🗨️",
    "Not every love story begins with 'once upon a time', but every great one ends with 'forever' 🌹",
]

TODAYS_COUPLE_LINES = [
    "🌸 These two — absolutely made for each other!",
    "💘 Fate brought them together, we're just witnessing history!",
    "🎯 It's not random, it's destiny — trust the algorithm of love!",
    "✨ Today's power couple has officially been revealed!",
    "🔥 This combination is pure fire — unstoppable!",
    "💫 A beautiful love story just began right here!",
    "🌺 The chemistry between these two is undeniable — science agrees!",
    "🎪 Step aside everyone — royalty has been crowned!",
    "🌊 They were two waves destined to crash into each other!",
    "🎵 Some songs were written just for couples like these!",
]


def _duration_fmt(seconds: int) -> str:
    td = timedelta(seconds=max(0, int(seconds)))
    days = td.days
    hours, rem = divmod(td.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    if days > 0:
        return f"{days} day{'s' if days != 1 else ''}"
    if hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    return f"{minutes} minute{'s' if minutes != 1 else ''}"


def _love_percent(id1: int, id2: int) -> int:
    seed = abs(id1 ^ id2 ^ (id1 + id2))
    random.seed(seed)
    pct = random.randint(70, 100)
    random.seed()
    return pct


def _love_bar(pct: int) -> str:
    filled = round(pct / 10)
    return "❤️" * filled + "🤍" * (10 - filled)


def _love_grade(pct: int) -> str:
    if pct >= 95:
        return "💍 Soulmates — Perfect Match!"
    if pct >= 85:
        return "🔥 Incredible Bond!"
    if pct >= 75:
        return "💕 Strong Connection!"
    return "🌱 Growing Love!"


def get_couple(user_id: int):
    try:
        return couples_col.find_one({"user_id": user_id})
    except Exception:
        return None


def make_couple(user_id: int, partner_id: int):
    now = int(time.time())
    try:
        for uid, pid in [(user_id, partner_id), (partner_id, user_id)]:
            couples_col.update_one(
                {"user_id": uid},
                {"$set": {"partner_id": pid, "since": now}},
                upsert=True,
            )
    except Exception:
        pass


def break_couple(user_id: int):
    try:
        doc = get_couple(user_id)
        if doc:
            couples_col.delete_one({"user_id": user_id})
            if doc.get("partner_id"):
                couples_col.delete_one({"user_id": doc["partner_id"]})
    except Exception:
        pass


try:
    register_gif_commands(app, "couple", "couple")
except Exception:
    pass


async def _resolve_target(client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    text = message.text or message.caption or ""
    entities = list(message.entities or []) + list(message.caption_entities or [])
    for ent in entities:
        try:
            etype = ent.type.value if hasattr(ent.type, "value") else str(ent.type)
        except Exception:
            continue
        if etype == "text_mention" and ent.user:
            return ent.user
        elif etype == "mention" and text:
            uname = text[ent.offset + 1: ent.offset + ent.length]
            try:
                return await client.get_users(uname)
            except Exception:
                pass
    return None


@app.on_message(filters.command("couple") & filters.group)
async def couple_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return

    target = await _resolve_target(client, message)

    if not target:
        return await message.reply(
            "<blockquote>💔 <b>Who do you want to couple with?</b>\n\n📌 Reply to someone's message with <code>/couple</code>\n📌 Or use <code>/couple @username</code></blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

    if target.id == user.id:
        return await message.reply(
            "<blockquote>😂 You can't couple with yourself!\nFind someone else — you deserve it! 💁</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

    if getattr(target, "is_bot", False):
        return await message.reply(
            "<blockquote>🤖 Bots are not capable of love!\nFind a real person to ship with 💝</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

    existing = get_couple(user.id)
    if existing:
        if existing.get("partner_id") == target.id:
            pct = _love_percent(user.id, target.id)
            duration = _duration_fmt(int(time.time()) - existing.get("since", int(time.time())))
            return await message.reply(
                f"<blockquote>💕 <b>You're already coupled!</b>\n\n❤️ {user.mention} + {target.mention}\n\n💖 <b>Love Meter:</b> {pct}%\n{_love_bar(pct)}\n<i>{_love_grade(pct)}</i>\n\n⏳ Together for: <b>{duration}</b></blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        return await message.reply(
            "<blockquote>💔 You're already in a couple!\nUse /uncouple first before shipping with someone new.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

    if get_couple(target.id):
        return await message.reply(
            f"<blockquote>💔 <b>{target.first_name}</b> is already in a couple with someone else!\nThey're taken 😔</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

    make_couple(user.id, target.id)
    pct = _love_percent(user.id, target.id)
    gif = get_random_gif("couple")

    caption = (
        f"<blockquote>"
        f"💑 <b>New Couple Alert! 🚨</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"❤️  {user.mention}\n"
        f"     💞 loves 💞\n"
        f"💕  {target.mention}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"💖 <b>Love Meter:</b> {pct}%\n"
        f"{_love_bar(pct)}\n"
        f"<b>{_love_grade(pct)}</b>\n\n"
        f"<i>✨ {random.choice(COUPLE_LINES)}</i>\n\n"
        f"🎊 Congratulations to this beautiful couple!"
        f"</blockquote>"
    )

    if gif:
        try:
            await client.send_animation(message.chat.id, gif, caption=caption, parse_mode=enums.ParseMode.HTML)
            return
        except Exception:
            pass
    await message.reply(caption, parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("uncouple") & filters.group)
async def uncouple_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return
    doc = get_couple(user.id)
    if not doc:
        return await message.reply(
            "<blockquote>💔 You're not in any couple right now.\nUse <code>/couple @user</code> to ship!</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    duration = _duration_fmt(int(time.time()) - doc.get("since", int(time.time())))
    partner_id = doc.get("partner_id")
    try:
        partner = await client.get_users(partner_id)
        p_mention = partner.mention
    except Exception:
        p_mention = f"User#{partner_id}"
    break_couple(user.id)
    await message.reply(
        f"<blockquote>💔 <b>Breakup Announcement</b>\n\n━━━━━━━━━━━━━━━━━━\n{user.mention} and {p_mention}\nhave decided to part ways.\n━━━━━━━━━━━━━━━━━━\n\n⏳ They were together for <b>{duration}</b>.\n\n<i>💫 Wishing both of them all the happiness in the world 🌸</i></blockquote>",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command("mycouple") & (filters.group | filters.private))
async def mycouple_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return
    doc = get_couple(user.id)
    if not doc:
        return await message.reply(
            "<blockquote>💔 <b>You're currently single!</b>\n\nNo partner found.\n\n💡 Use <code>/couple @username</code> to ship with someone!</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    partner_id = doc.get("partner_id")
    pct = _love_percent(user.id, partner_id)
    duration = _duration_fmt(int(time.time()) - doc.get("since", int(time.time())))
    try:
        partner = await client.get_users(partner_id)
        p_mention = partner.mention
    except Exception:
        p_mention = f"User#{partner_id}"
    await message.reply(
        f"<blockquote>💕 <b>Your Couple Status</b>\n\n━━━━━━━━━━━━━━━━━━\n❤️ {user.mention}\n💕 {p_mention}\n━━━━━━━━━━━━━━━━━━\n\n💖 <b>Love Meter:</b> {pct}%\n{_love_bar(pct)}\n<b>{_love_grade(pct)}</b>\n\n⏳ <b>Together for:</b> {duration}</blockquote>",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command("couples") & filters.group)
async def couples_random_cmd(client, message: Message):
    members = []
    try:
        async for member in client.get_chat_members(message.chat.id):
            if member.user and not member.user.is_bot and not member.user.is_deleted:
                members.append(member.user)
    except Exception as e:
        return await message.reply(
            f"<blockquote>❌ <b>Could not fetch group members!</b>\n\nMake sure the bot has admin rights.\nError: <code>{e}</code></blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    if len(members) < 2:
        return await message.reply("<blockquote>😅 Need at least 2 real members to ship!</blockquote>", parse_mode=enums.ParseMode.HTML)

    u1, u2 = random.sample(members, 2)
    pct = _love_percent(u1.id, u2.id)
    gif = get_random_gif("couple")

    caption = (
        f"<blockquote>"
        f"💘 <b>Today's Featured Couple! 🏆</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"❤️  {u1.mention}\n"
        f"     ❤️‍🔥 ➤ ➤ ➤\n"
        f"💕  {u2.mention}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"💖 <b>Love Meter:</b> {pct}%\n"
        f"{_love_bar(pct)}\n"
        f"<b>{_love_grade(pct)}</b>\n\n"
        f"<i>✨ {random.choice(TODAYS_COUPLE_LINES)}</i>"
        f"</blockquote>"
    )

    if gif:
        try:
            await client.send_animation(message.chat.id, gif, caption=caption, parse_mode=enums.ParseMode.HTML)
            return
        except Exception:
            pass
    await message.reply(caption, parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("couplerank") & filters.group)
async def couplerank_cmd(client, message: Message):
    try:
        all_docs = list(couples_col.find().sort("since", 1))
    except Exception:
        return await message.reply("<blockquote>❌ Database error. Please try again later.</blockquote>", parse_mode=enums.ParseMode.HTML)

    seen, ranked = set(), []
    for doc in all_docs:
        u_id = doc.get("user_id")
        p_id = doc.get("partner_id")
        if not u_id or not p_id:
            continue
        pair = tuple(sorted([u_id, p_id]))
        if pair not in seen:
            seen.add(pair)
            ranked.append((pair, doc.get("since", int(time.time()))))

    if not ranked:
        return await message.reply("<blockquote>💔 No couples yet!\nBe the first — use <code>/couple @user</code></blockquote>", parse_mode=enums.ParseMode.HTML)

    now = int(time.time())
    medals = ["🥇", "🥈", "🥉"]
    text = "<blockquote>🏆 <b>Top Couples Leaderboard</b>\n\n"
    for i, (pair, since) in enumerate(ranked[:10]):
        medal = medals[i] if i < 3 else f"{i + 1}."
        pct = _love_percent(pair[0], pair[1])
        try:
            u1 = await client.get_users(pair[0])
            u2 = await client.get_users(pair[1])
            names = f"{u1.first_name} ❤️ {u2.first_name}"
        except Exception:
            names = f"ID#{pair[0]} ❤️ ID#{pair[1]}"
        text += f"{medal} {names}\n     💖{pct}% | ⏳{_duration_fmt(now - since)}\n\n"
    text += "</blockquote>"
    await message.reply(text, parse_mode=enums.ParseMode.HTML)
