"""
Couple Plugin for HasiiMusicBot
Commands:
  /couple @user      - Ship yourself with mentioned user
  /uncouple          - Break up with your current partner
  /mycouple          - Show your current couple status
  /couples           - Randomly ship two group members together
  /couplerank        - Top couples in this group (by days together)

Couple GIFs auto-rotate on each /couple command.
"""

import random
import time
from datetime import timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient as PyMongoClient

# ─── COUPLE GIF FILE IDs (from your pasted raw data) ─────────────────────────
COUPLE_GIFS = [
    "CgACAgQAAxkBAAFK9NVqGYk7xGGp2pAGKupttLxHLImdNAACywgAAlbJrFHKM99F2lJZNjsE",  # anime-spy-x-family
    "CgACAgQAAxkBAAFK9NdqGYlJRLjZxUlz6jec9SLLVAVZnQACIAoAApdj3FK7a0fitBb2rjsE",  # hug-anime
    "CgACAgQAAxkBAAFK9NtqGYltnBtoCk7VxU3EJ300kL99uwAClgoAAhFTVFGKWgZh40VeIjsE",  # anime-comfort-hug
    "CgACAgQAAxkBAAFK9OpqGYmyFoqnLKhJv0SphjfTUPupawAC4gQAAhZQHFHHpA-xsiUtfjsE",  # hug
]

# ─── DB ──────────────────────────────────────────────────────────────────────
try:
    from HasiiMusic.core.mongo import mongodb as db
except ImportError:
    import os
    _client = PyMongoClient(os.getenv("MONGO_DB_URI", "mongodb://localhost:27017"))
    db = _client["HasiiMusicBot"]

couples_col = db["couples"]


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


def get_couple(user_id: int):
    return couples_col.find_one({"user_id": user_id})


def get_couple_of(user_id: int):
    """Find the couple record where this user is the partner."""
    return couples_col.find_one({"partner_id": user_id})


def make_couple(user_id: int, partner_id: int):
    now = int(time.time())
    # Store both directions so both users can look up
    couples_col.update_one(
        {"user_id": user_id},
        {"$set": {"partner_id": partner_id, "since": now}},
        upsert=True,
    )
    couples_col.update_one(
        {"user_id": partner_id},
        {"$set": {"partner_id": user_id, "since": now}},
        upsert=True,
    )


def break_couple(user_id: int):
    doc = get_couple(user_id)
    if doc:
        partner_id = doc.get("partner_id")
        couples_col.delete_one({"user_id": user_id})
        if partner_id:
            couples_col.delete_one({"user_id": partner_id})


# ─── /couple ─────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("couple") & filters.group)
async def couple_cmd(client: Client, message: Message):
    user = message.from_user

    # Must mention or reply to someone
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif message.entities:
        for ent in message.entities:
            if ent.type.value == "text_mention" and ent.user:
                target = ent.user
                break
            elif ent.type.value == "mention" and message.text:
                uname = message.text[ent.offset + 1 : ent.offset + ent.length]
                try:
                    target = await client.get_users(uname)
                    break
                except Exception:
                    pass

    if not target:
        return await message.reply("💔 Mention or reply to the user you want to couple with!")

    if target.id == user.id:
        return await message.reply("😂 You can't couple with yourself!")

    if target.is_bot:
        return await message.reply("🤖 You can't couple with a bot!")

    # Check if already coupled
    existing = get_couple(user.id)
    if existing:
        if existing["partner_id"] == target.id:
            return await message.reply(
                f"💕 You're already coupled with {target.mention}!", parse_mode="html"
            )
        return await message.reply(
            "💔 You're already in a couple! Use /uncouple first."
        )

    # Check if target is already coupled
    target_existing = get_couple(target.id)
    if target_existing:
        return await message.reply(
            f"💔 {target.mention} is already in a couple!", parse_mode="html"
        )

    make_couple(user.id, target.id)

    gif = random.choice(COUPLE_GIFS)
    caption = (
        f"💑 **New Couple Alert!**\n\n"
        f"💕 {user.mention} ❤️ {target.mention}\n\n"
        f"Congratulations to the new couple! 🎉"
    )
    await client.send_animation(
        message.chat.id, gif, caption=caption, parse_mode="html"
    )


# ─── /uncouple ───────────────────────────────────────────────────────────────
@Client.on_message(filters.command("uncouple") & filters.group)
async def uncouple_cmd(client: Client, message: Message):
    user = message.from_user
    doc = get_couple(user.id)

    if not doc:
        return await message.reply("💔 You're not in a couple right now.")

    partner_id = doc.get("partner_id")
    duration = _days_fmt(int(time.time()) - doc.get("since", int(time.time())))

    try:
        partner = await client.get_users(partner_id)
        partner_mention = partner.mention
    except Exception:
        partner_mention = f"User#{partner_id}"

    break_couple(user.id)
    await message.reply(
        f"💔 {user.mention} and {partner_mention} have broken up after **{duration}** together.\n\n"
        f"Hope you both find happiness! 🌸",
        parse_mode="html",
    )


# ─── /mycouple ───────────────────────────────────────────────────────────────
@Client.on_message(filters.command("mycouple") & (filters.group | filters.private))
async def mycouple_cmd(client: Client, message: Message):
    user = message.from_user
    doc = get_couple(user.id)

    if not doc:
        return await message.reply("💔 You're currently single. Use /couple @user to ship yourself!")

    partner_id = doc.get("partner_id")
    duration = _days_fmt(int(time.time()) - doc.get("since", int(time.time())))

    try:
        partner = await client.get_users(partner_id)
        partner_mention = partner.mention
    except Exception:
        partner_mention = f"User#{partner_id}"

    await message.reply(
        f"💕 **Your Couple Status**\n\n"
        f"💑 Partner: {partner_mention}\n"
        f"⏳ Together for: **{duration}**",
        parse_mode="html",
    )


# ─── /couples (random ship two group members) ────────────────────────────────
@Client.on_message(filters.command("couples") & filters.group)
async def couples_random_cmd(client: Client, message: Message):
    members = []
    async for member in client.get_chat_members(message.chat.id):
        if not member.user.is_bot and not member.user.is_deleted:
            members.append(member.user)

    if len(members) < 2:
        return await message.reply("😅 Not enough members in this group to ship!")

    # Pick 2 unique random members
    user1, user2 = random.sample(members, 2)

    gif = random.choice(COUPLE_GIFS)
    caption = (
        f"💘 **Today's Random Couple!**\n\n"
        f"💕 {user1.mention} ❤️ {user2.mention}\n\n"
        f"Aaj ke liye yeh dono perfect match hain! 🌸✨"
    )
    await client.send_animation(
        message.chat.id, gif, caption=caption, parse_mode="html"
    )


# ─── /couplerank ─────────────────────────────────────────────────────────────
@Client.on_message(filters.command("couplerank") & filters.group)
async def couplerank_cmd(client: Client, message: Message):
    # Get all couples, sorted by time together (oldest first = longest)
    all_docs = list(couples_col.find().sort("since", 1))

    # Deduplicate pairs (A-B and B-A are same couple)
    seen = set()
    ranked = []
    for doc in all_docs:
        pair = tuple(sorted([doc["user_id"], doc["partner_id"]]))
        if pair in seen:
            continue
        seen.add(pair)
        ranked.append((pair, doc.get("since", int(time.time()))))

    if not ranked:
        return await message.reply("💔 No couples registered yet!")

    now = int(time.time())
    text = "🏆 **Couple Rankings**\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, (pair, since) in enumerate(ranked[:10]):
        medal = medals[i] if i < 3 else f"{i + 1}."
        duration = _days_fmt(now - since)
        try:
            u1 = await client.get_users(pair[0])
            u2 = await client.get_users(pair[1])
            text += f"{medal} {u1.first_name} ❤️ {u2.first_name} — **{duration}**\n"
        except Exception:
            text += f"{medal} ID#{pair[0]} ❤️ ID#{pair[1]} — **{duration}**\n"

    await message.reply(text, parse_mode="html")
