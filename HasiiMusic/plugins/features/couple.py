"""
Couple Plugin — v3 FIXED
Commands:
  /couple @user   - Ship yourself with someone
  /uncouple       - Break up
  /mycouple       - Check your couple status
  /couples        - Random couple from group members
  /couplerank     - Top couples by duration

GIF Management (owner/sudo/admin only):
  /setcouplegif   - Reply to GIF → add to couple list
  /rmcouplegif <n>- Remove couple GIF by number
  /listcouplegif  - See all couple GIFs

FIX: @Client.on_message → @app.on_message  (yahi main bug tha)
"""

import random
import time
from datetime import timedelta

from pyrogram import filters
from pyrogram.types import Message
from pymongo import MongoClient as PyMongoClient

from HasiiMusic.helpers.gif_manager import get_random_gif, register_gif_commands
from HasiiMusic import app

try:
    from HasiiMusic.core.mongo import mongodb as _db
except ImportError:
    import os
    _c = PyMongoClient(os.getenv("MONGO_DB_URI", "mongodb://localhost:27017"))
    _db = _c["HasiiMusicBot"]

couples_col = _db["couples"]

COUPLE_LINES = [
    "Dil ne dil ko dhundha, mil gaye 💞",
    "Tumhara pyaar hi meri duniya hai 🌍❤️",
    "Teri baahon mein ek alag hi sukoon hai 💑",
    "Mohabbat ka doosra naam hai — tum 💓",
    "Aaj ke couple ne dil jeet liya! 🏆❤️",
    "Yeh do dil, ek hi dhadkan 💗",
    "Saath rehna hai, bichadna nahi — yahi hai saccha pyaar 🌺",
    "Tumhari hansi pe mera dil fida hai 😍",
    "Aankh uthi aur tum the samne — kismat ne milaya 💫",
    "Log aate jaate hain, tum reh jaate ho ❣️",
    "Ye wala pyaar wali baat hai boss! 😘",
    "Ship ho gaye officially — ab toh pakka hai 🚢❤️",
]

TODAYS_COUPLE_LINES = [
    "🌸 Aaj ke liye yeh dono — made for each other!",
    "💘 Fate ne milaya, aur hum ship kar rahe hain!",
    "🎯 Random nahi, destiny hai yaar!",
    "✨ Aaj ka power couple reveal ho gaya!",
    "🔥 Yeh combination toh ek dum fire hai!",
    "💫 Aaj ki love story start ho gayi!",
    "🌺 Dono mein chemistry hai bhai — pakki baat!",
]


def _days_fmt(seconds: int) -> str:
    td = timedelta(seconds=seconds)
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
    pct = random.randint(65, 100)
    random.seed()
    return pct


def _love_bar(pct: int) -> str:
    filled = round(pct / 10)
    return "❤️" * filled + "🖤" * (10 - filled)


def get_couple(user_id: int):
    return couples_col.find_one({"user_id": user_id})


def make_couple(user_id: int, partner_id: int):
    now = int(time.time())
    for uid, pid in [(user_id, partner_id), (partner_id, user_id)]:
        couples_col.update_one(
            {"user_id": uid},
            {"$set": {"partner_id": pid, "since": now}},
            upsert=True,
        )


def break_couple(user_id: int):
    doc = get_couple(user_id)
    if doc:
        couples_col.delete_one({"user_id": user_id})
        if doc.get("partner_id"):
            couples_col.delete_one({"user_id": doc["partner_id"]})


# ─── GIF management commands ─────────────────────────────────────────────────
register_gif_commands(app, "couple", "couple")


# ─── /couple ─────────────────────────────────────────────────────────────────
@app.on_message(filters.command("couple") & filters.group)
async def couple_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return
    target = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif message.entities:
        for ent in message.entities:
            if ent.type.value == "text_mention" and ent.user:
                target = ent.user
                break
            elif ent.type.value == "mention" and message.text:
                uname = message.text[ent.offset + 1: ent.offset + ent.length]
                try:
                    target = await client.get_users(uname)
                    break
                except Exception:
                    pass

    if not target:
        return await message.reply(
            "<blockquote>💔 Mention ya reply karo jis se couple banana hai!\n\n"
            "Usage: <code>/couple @username</code>\n"
            "Ya kisi message ko reply karke <code>/couple</code> likho</blockquote>",
            parse_mode="html"
        )
    if target.id == user.id:
        return await message.reply(
            "<blockquote>😂 Apne aap se couple nahi ban sakte!</blockquote>"
        )
    if target.is_bot:
        return await message.reply(
            "<blockquote>🤖 Bot se couple nahi ban sakte!</blockquote>"
        )

    existing = get_couple(user.id)
    if existing:
        if existing["partner_id"] == target.id:
            pct = _love_percent(user.id, target.id)
            return await message.reply(
                f"<blockquote>💕 Tum already {target.mention} ke saath couple ho!\n"
                f"💖 Love: <b>{pct}%</b> {_love_bar(pct)}</blockquote>",
                parse_mode="html"
            )
        return await message.reply(
            "<blockquote>💔 Tum already ek couple mein ho! Pehle /uncouple karo.</blockquote>"
        )

    if get_couple(target.id):
        return await message.reply(
            f"<blockquote>💔 {target.mention} already kisi aur ke saath couple mein hai!</blockquote>",
            parse_mode="html"
        )

    make_couple(user.id, target.id)

    pct = _love_percent(user.id, target.id)
    gif = get_random_gif("couple")
    caption = (
        f"<blockquote>"
        f"💑 <b>Naya Couple Alert!</b>\n\n"
        f"❤️ {user.mention}\n"
        f"╰┈➤ loves ➤\n"
        f"💕 {target.mention}\n\n"
        f"💖 <b>Love Meter:</b> {pct}%\n"
        f"{_love_bar(pct)}\n\n"
        f"<i>{random.choice(COUPLE_LINES)}</i>\n\n"
        f"🎉 Congratulations to the new couple!"
        f"</blockquote>"
    )

    if gif:
        try:
            await client.send_animation(message.chat.id, gif, caption=caption, parse_mode="html")
            return
        except Exception:
            pass
    await message.reply(caption, parse_mode="html")


# ─── /uncouple ───────────────────────────────────────────────────────────────
@app.on_message(filters.command("uncouple") & filters.group)
async def uncouple_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return
    doc = get_couple(user.id)
    if not doc:
        return await message.reply(
            "<blockquote>💔 Tum abhi kisi couple mein nahi ho.</blockquote>"
        )

    duration = _days_fmt(int(time.time()) - doc.get("since", int(time.time())))
    try:
        partner = await client.get_users(doc.get("partner_id"))
        p_mention = partner.mention
    except Exception:
        p_mention = f"User#{doc.get('partner_id')}"

    break_couple(user.id)
    await message.reply(
        f"<blockquote>"
        f"💔 {user.mention} aur {p_mention} ne breakup kar liya.\n"
        f"⏳ <b>{duration}</b> saath bitaye the.\n\n"
        f"<i>Dono ko aage ki zindagi mein khushiyaan milein 🌸</i>"
        f"</blockquote>",
        parse_mode="html",
    )


# ─── /mycouple ───────────────────────────────────────────────────────────────
@app.on_message(filters.command("mycouple") & (filters.group | filters.private))
async def mycouple_cmd(client, message: Message):
    user = message.from_user
    if not user:
        return
    doc = get_couple(user.id)
    if not doc:
        return await message.reply(
            "<blockquote>💔 Tum abhi single ho.\n💡 Use /couple @user to ship!</blockquote>"
        )

    partner_id = doc.get("partner_id")
    pct = _love_percent(user.id, partner_id)
    try:
        partner = await client.get_users(partner_id)
        p_mention = partner.mention
    except Exception:
        p_mention = f"User#{partner_id}"

    await message.reply(
        f"<blockquote>"
        f"💕 <b>Tumhara Couple Status</b>\n\n"
        f"💑 Partner: {p_mention}\n"
        f"⏳ Saath: <b>{_days_fmt(int(time.time()) - doc.get('since', int(time.time())))}</b>\n"
        f"💖 Love: <b>{pct}%</b>\n{_love_bar(pct)}"
        f"</blockquote>",
        parse_mode="html",
    )


# ─── /couples — random pair from group members ───────────────────────────────
@app.on_message(filters.command("couples") & filters.group)
async def couples_random_cmd(client, message: Message):
    members = []
    try:
        async for member in client.get_chat_members(message.chat.id):
            if not member.user.is_bot and not member.user.is_deleted:
                members.append(member.user)
    except Exception as e:
        return await message.reply(
            f"<blockquote>❌ Members fetch nahi ho sake: {e}</blockquote>"
        )

    if len(members) < 2:
        return await message.reply(
            "<blockquote>😅 Group mein kam se kam 2 members chahiye!</blockquote>"
        )

    u1, u2 = random.sample(members, 2)
    pct = _love_percent(u1.id, u2.id)
    gif = get_random_gif("couple")

    caption = (
        f"<blockquote>"
        f"💘 <b>Today's Best Couple! 🏆</b>\n\n"
        f"❤️ {u1.mention}\n╰┈➤ ❤️‍🔥 ➤\n💕 {u2.mention}\n\n"
        f"💖 <b>Love Meter:</b> {pct}%\n{_love_bar(pct)}\n\n"
        f"<i>{random.choice(TODAYS_COUPLE_LINES)}</i>"
        f"</blockquote>"
    )

    if gif:
        try:
            await client.send_animation(message.chat.id, gif, caption=caption, parse_mode="html")
            return
        except Exception:
            pass
    await message.reply(caption, parse_mode="html")


# ─── /couplerank ─────────────────────────────────────────────────────────────
@app.on_message(filters.command("couplerank") & filters.group)
async def couplerank_cmd(client, message: Message):
    all_docs = list(couples_col.find().sort("since", 1))
    seen, ranked = set(), []
    for doc in all_docs:
        pair = tuple(sorted([doc["user_id"], doc["partner_id"]]))
        if pair not in seen:
            seen.add(pair)
            ranked.append((pair, doc.get("since", int(time.time()))))

    if not ranked:
        return await message.reply(
            "<blockquote>💔 Abhi koi couple registered nahi hai!</blockquote>"
        )

    now = int(time.time())
    text = "<blockquote>🏆 <b>Best Couples Ranking</b>\n\n"
    for i, (pair, since) in enumerate(ranked[:10]):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
        pct = _love_percent(pair[0], pair[1])
        try:
            u1 = await client.get_users(pair[0])
            u2 = await client.get_users(pair[1])
            text += f"{medal} {u1.first_name} ❤️ {u2.first_name} — <b>{_days_fmt(now - since)}</b> | 💖{pct}%\n"
        except Exception:
            text += f"{medal} ID#{pair[0]} ❤️ ID#{pair[1]} — <b>{_days_fmt(now - since)}</b> | 💖{pct}%\n"
    text += "</blockquote>"

    await message.reply(text, parse_mode="html")
