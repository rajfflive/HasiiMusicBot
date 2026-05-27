import random
import hashlib
from datetime import datetime

from pyrogram import filters, types
from pyrogram.errors import ChatAdminRequired, UserNotParticipant

from HasiiMusic import app

COUPLE_GIFS = [
    "https://media.giphy.com/media/l0MYB8Ory7Hqefo9a/giphy.gif",
    "https://media.giphy.com/media/3o6ZtaO9BZHcOjmErm/giphy.gif",
    "https://media.giphy.com/media/l4FGni1RBAR2OWsGk/giphy.gif",
    "https://media.giphy.com/media/xT9IgG50Lg7russbDa/giphy.gif",
    "https://media.giphy.com/media/3oEdv9Y9mdCQPNkPqw/giphy.gif",
    "https://media.giphy.com/media/LpkBAUDg53FI8xLmqL/giphy.gif",
    "https://media.giphy.com/media/4WEtA5LMtPAta/giphy.gif",
    "https://media.giphy.com/media/TJ2sOWrC6TMjK/giphy.gif",
]

COUPLE_MSGS = [
    "💑 Aaj ke couple hain:\n\n{p1} ❤️ {p2}\n\n🌹 Dono bohot acche lagte hain saath mein!",
    "💘 Today's Couple:\n\n{p1} 💕 {p2}\n\n✨ Match made in heaven!",
    "🔥 Aaj ki jodi:\n\n{p1} 🥰 {p2}\n\n💫 Yeh toh perfect couple hai!",
    "💞 Group ki nayi jodi:\n\n{p1} 💖 {p2}\n\n🎉 Congratulations to today's couple!",
    "🌸 Aaj ke liye couple ban gaye:\n\n{p1} 💗 {p2}\n\n😍 Sach mein bohot cute couple hai!",
]

_daily_couples: dict = {}


def _get_daily_seed(chat_id: int) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{chat_id}-{today}"


@app.on_message(filters.command(["couple"]) & filters.group)
async def couple_cmd(_, m: types.Message):
    chat_id = m.chat.id
    seed = _get_daily_seed(chat_id)

    if seed in _daily_couples:
        p1_id, p2_id = _daily_couples[seed]
        try:
            p1 = await app.get_users(p1_id)
            p2 = await app.get_users(p2_id)
        except Exception:
            del _daily_couples[seed]
            return await m.reply_text("<blockquote><b>❌ Couple data expired, try again!</b></blockquote>")

        text = random.choice(COUPLE_MSGS).format(
            p1=p1.mention,
            p2=p2.mention,
        )
        gif = COUPLE_GIFS[int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(COUPLE_GIFS)]
        return await m.reply_animation(
            gif,
            caption=f"<blockquote><b>💑 Aaj Ka Couple (Already Decided!)</b></blockquote>\n\n{text}"
        )

    members = []
    try:
        async for member in app.get_chat_members(chat_id):
            if not member.user.is_bot and not member.user.is_deleted:
                members.append(member.user)
    except ChatAdminRequired:
        return await m.reply_text(
            "<blockquote><b>❌ Bot ko admin banana padega members dekhne ke liye!</b></blockquote>"
        )

    if len(members) < 2:
        return await m.reply_text(
            "<blockquote><b>❌ Group mein kam se kam 2 members chahiye!</b></blockquote>"
        )

    seed_int = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    random.seed(seed_int)
    chosen = random.sample(members, 2)
    random.seed()

    p1, p2 = chosen[0], chosen[1]
    _daily_couples[seed] = (p1.id, p2.id)

    text = random.choice(COUPLE_MSGS).format(
        p1=p1.mention,
        p2=p2.mention,
    )
    gif = COUPLE_GIFS[seed_int % len(COUPLE_GIFS)]

    await m.reply_animation(
        gif,
        caption=f"<blockquote><b>💑 Aaj Ka Couple</b></blockquote>\n\n{text}\n\n"
                f"<blockquote><i>Yeh couple sirf aaj ke liye hai 😄</i></blockquote>"
    )


@app.on_message(filters.command(["ship"]) & filters.group)
async def ship_cmd(_, m: types.Message):
    if not m.reply_to_message:
        if len(m.command) < 2:
            return await m.reply_text(
                "<blockquote><b>Usage:</b>\n"
                "Reply karo kisi pe: <code>/ship</code>\n"
                "Ya mention karo: <code>/ship @user1 @user2</code></blockquote>"
            )

    try:
        user1 = m.from_user
        if m.reply_to_message:
            user2 = m.reply_to_message.from_user
        else:
            entities = [e for e in (m.entities or []) if e.type.name == "MENTION"]
            if len(entities) >= 2:
                text = m.text
                u2_name = text[entities[1].offset + 1: entities[1].offset + entities[1].length]
                user2 = await app.get_users(u2_name)
            else:
                return await m.reply_text("<blockquote><b>❌ Dono users mention karo!</b></blockquote>")

        combined = f"{user1.id}{user2.id}"
        score = int(hashlib.md5(combined.encode()).hexdigest(), 16) % 101
        bar_filled = int(score / 10)
        bar = "❤️" * bar_filled + "🖤" * (10 - bar_filled)

        if score >= 80:
            verdict = "💘 Perfect Match! Shaadi kab hai?"
        elif score >= 60:
            verdict = "💖 Bohot accha couple banega!"
        elif score >= 40:
            verdict = "💛 Thodi mehnat aur karni padegi."
        elif score >= 20:
            verdict = "🤔 Dono mein kuch toh hai..."
        else:
            verdict = "💔 Yeh toh mushkil hai bhai..."

        await m.reply_text(
            f"<blockquote><b>💕 Ship Meter</b></blockquote>\n\n"
            f"<blockquote>{user1.mention} + {user2.mention}\n\n"
            f"{bar}\n"
            f"Score: <b>{score}%</b>\n\n"
            f"{verdict}</blockquote>"
        )
    except Exception as e:
        await m.reply_text(f"<blockquote><b>❌ Error: {e}</b></blockquote>")
