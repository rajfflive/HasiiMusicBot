import random
import asyncio
import time

from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from HasiiMusic import app

# ── Data ──────────────────────────────────────────────────────────────────────

TRUTH_QUESTIONS = [
    "Aapki zindagi ka sabse sharmindagi wala moment kaunsa tha?",
    "Aapne kabhi kisi ka secret share kiya? Kiska?",
    "Aap group mein kisse sabse zyada pasand karte ho?",
    "Aapne kabhi kisi pe crush kiya group mein? 👀",
    "Aapki worst date kaisi thi?",
    "Aapne kabhi exam mein cheat kiya?",
    "Aapki sabse badi weakness kya hai?",
    "Aapne aakhri baar kab jhooth bola aur kisliye?",
    "Agar time travel kar sako toh kaunsa moment badloge?",
    "Aapka sabse bada darna kya hai?",
    "Aapne kabhi kisi ki burai ki peethe peeche?",
    "Aapki secret talent kya hai jo koi nahi jaanta?",
    "Pehli nazar mein pyaar hota hai? Tumhara kya experience hai?",
    "Aapne aakhri baar kab roya aur kisliye?",
    "Agar ek din ke liye invisible ho jao toh kya karoge?",
]

DARE_CHALLENGES = [
    "Apna WhatsApp status 1 ghante ke liye 'Main pagal hoon' rakhna! 😂",
    "Group mein apni embarrassing photo bhejni hai!",
    "Abhi is waqt kisi bhi contact ko 'I love you' message karo! 😏",
    "Apni awaaz mein koi filmy dialogue sunao group voice note mein!",
    "Apna naam ulta bolke voice note bhejo!",
    "Apne favourite celebrity ki mimicry karo voice note mein!",
    "Group mein ek shayari sunao abhi!",
    "10 baar tezi se 'Kala Coat Peela Coat' bolo voice note mein!",
    "Apna favourite gaana 30 second ke liye humming karo!",
    "Group mein apna ek embarrassing secret share karo!",
    "Abhi apni maa ko call karke poocho 'Tumhara favourite child kaun hai?'",
    "Apne profile picture pe next 2 ghante ke liye cartoon lagao!",
    "10 pushups karo aur proof photo bhejo!",
    "Abhi jo sabse pehle dimaag mein aaye use 'Tu mera hero hai' bolke message karo!",
]

WYR_QUESTIONS = [
    ("Hamesha nanga peethe ghoomna", "Hamesha formal suit mein rehna"),
    ("Sab kuch sun sako lekin dekh na sako", "Sab kuch dekh sako lekin sun na sako"),
    ("Udd sako", "Paani ke andar sans le sako"),
    ("Hamesha ek hi khana khao", "Kabhi khana na khao (energy pills se kaam chale)"),
    ("10 saal aur jiyo magar perfect health mein", "50 saal aur jiyo magar bemar rehke"),
    ("Hamesha sach bolo", "Kabhi sach na bolo"),
    ("Sirf din mein jio (raat nahi)", "Sirf raat mein jio (din nahi)"),
    ("Gana bohot accha gao lekin dance na kar pao", "Dance bohot accha karo lekin gana na ga pao"),
    ("Har jagah free delivery milti rahe", "Har jagah free wifi milta rahe"),
    ("Famous ho magar garib raho", "Rich ho magar anonymous raho"),
    ("Apna past badal sako", "Apna future dekh sako"),
    ("Hamesha khush raho lekin broke raho", "Hamesha ameer raho lekin sad raho"),
]

RIDDLES = [
    ("Main har roz marta hoon lekin kabhi khatum nahi hota. Main kaun hoon?", "Kal (Din)"),
    ("Jitna lo utna zyada ho jaata hoon. Main kaun hoon?", "Ek Gaddha (Khudai)"),
    ("Mere paas haath hain magar main chhoo nahi sakta. Main kaun hoon?", "Ghadi"),
    ("Main bolta hoon bina zubaan ke, main sunta hoon bina kaan ke. Main kaun hoon?", "Echo"),
    ("Tum mujhe khareedo lekin kabhi use nahi karte, doosre use karte hain. Main kaun hoon?", "Taboot"),
    ("Main sabse fast daudta hoon bina paon ke. Main kaun hoon?", "Waqt"),
    ("Jitna sukha ho utna bhaari, geela ho toh halka. Main kaun hoon?", "Sponge"),
    ("Ek kamra hai jisme koi darwaza nahi, koi khidki nahi. Log andar kaise gaye?", "Andar pehle se the"),
    ("Main aage se padho ya peeche se, main same rahoon. Main kaun hoon?", "Palindrome (e.g. ANA)"),
    ("Main hamesha aata hoon lekin kabhi nahi pohonchta. Main kaun hoon?", "Kal"),
]

ROASTS = [
    "Teri photo itni blur hai jaise tere future plans! 😂",
    "Tu itna slow hai ki Wi-Fi bhi tujhse tez hai! 📶",
    "Tere jokes sun ke log seriously sochte hain ki hasein ya roein! 💀",
    "Teri personality utni interesting hai jitna blank page hota hai! 📄",
    "Tu homework ki tarah hai — sabse zyada avoid kiya jaata hai! 📚",
    "Tere saath time spend karna ek experience hai... negative wala! 😅",
    "Teri cooking itni buri hai ki gharka kuttta bhi nahi khaata! 🐶",
    "Tu itna boring hai ki apni neend bhi tujhse baat nahi karta! 😴",
    "Teri advice itni useful hai jitna paani mein aag laganaaaaaaa! 🔥",
    "Tu trophy ki tarah hai — display pe achha lagta hai kaam ka nahi! 🏆",
]

COMPLIMENTS = [
    "Tu is group ka sabse bright star hai! ⭐",
    "Tujhse baat karke mood fresh ho jaata hai! 🌸",
    "Teri smile itni pyaari hai ki dil khush ho jaata hai! 😊",
    "Tu genuinely ek bohot accha insaan hai! 💖",
    "Tere thoughts itne unique hain ki sab sochte reh jaate hain! 🧠",
    "Duniya mein tere jaise log bohot kam hain! 🌟",
    "Tu jo bhi kare usme 100% deta hai — yeh mujhe pasand hai! 💪",
    "Tere saath rahke sab kuch easy lagta hai! 🤗",
    "Tu ek walking positive energy hai! ✨",
    "Tujhe jaanke meri zindagi better ho gayi! 💫",
]

# ── Active game sessions ───────────────────────────────────────────────────────
_active_riddles: dict = {}
_active_wyr: dict = {}


# ── Truth or Dare ─────────────────────────────────────────────────────────────

@app.on_message(filters.command(["tnd", "truthordare"]) & filters.group)
async def tod_cmd(_, m: types.Message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤔 Truth", callback_data="tod_truth"),
            InlineKeyboardButton("😈 Dare", callback_data="tod_dare"),
        ]
    ])
    await m.reply_text(
        f"<blockquote><b>🎮 Truth or Dare!</b></blockquote>\n\n"
        f"<blockquote>{m.from_user.mention} ne game shuru kiya!\nChuno kya loge:</blockquote>",
        reply_markup=keyboard
    )


@app.on_callback_query(filters.regex("^tod_truth$"))
async def tod_truth_cb(_, q: types.CallbackQuery):
    question = random.choice(TRUTH_QUESTIONS)
    await q.answer()
    await q.message.edit_text(
        f"<blockquote><b>🤔 TRUTH</b></blockquote>\n\n"
        f"<blockquote>{q.from_user.mention}, tumhara sawaal:\n\n"
        f"<b>{question}</b></blockquote>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Dobara Khelo", callback_data="tod_restart")]
        ])
    )


@app.on_callback_query(filters.regex("^tod_dare$"))
async def tod_dare_cb(_, q: types.CallbackQuery):
    dare = random.choice(DARE_CHALLENGES)
    await q.answer()
    await q.message.edit_text(
        f"<blockquote><b>😈 DARE</b></blockquote>\n\n"
        f"<blockquote>{q.from_user.mention}, tumhara dare:\n\n"
        f"<b>{dare}</b></blockquote>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Dobara Khelo", callback_data="tod_restart")]
        ])
    )


@app.on_callback_query(filters.regex("^tod_restart$"))
async def tod_restart_cb(_, q: types.CallbackQuery):
    await q.answer()
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤔 Truth", callback_data="tod_truth"),
            InlineKeyboardButton("😈 Dare", callback_data="tod_dare"),
        ]
    ])
    await q.message.edit_text(
        f"<blockquote><b>🎮 Truth or Dare!</b></blockquote>\n\n"
        f"<blockquote>{q.from_user.mention} ne dobara khela!\nChuno:</blockquote>",
        reply_markup=keyboard
    )


# ── Would You Rather ──────────────────────────────────────────────────────────

@app.on_message(filters.command(["wyr", "wouldyourather"]) & filters.group)
async def wyr_cmd(_, m: types.Message):
    opt_a, opt_b = random.choice(WYR_QUESTIONS)
    chat_id = m.chat.id
    msg = await m.reply_text(
        f"<blockquote><b>🤯 Would You Rather?</b></blockquote>\n\n"
        f"<blockquote>🅰️ <b>{opt_a}</b>\n\n"
        f"ya\n\n"
        f"🅱️ <b>{opt_b}</b></blockquote>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"🅰️ Option A (0)", callback_data=f"wyr_a_{m.id}"),
                InlineKeyboardButton(f"🅱️ Option B (0)", callback_data=f"wyr_b_{m.id}"),
            ]
        ])
    )
    _active_wyr[f"{chat_id}_{m.id}"] = {
        "opt_a": opt_a, "opt_b": opt_b,
        "votes_a": set(), "votes_b": set()
    }


@app.on_callback_query(filters.regex(r"^wyr_(a|b)_(\d+)$"))
async def wyr_vote_cb(_, q: types.CallbackQuery):
    choice = q.matches[0].group(1)
    msg_id = q.matches[0].group(2)
    key = f"{q.message.chat.id}_{msg_id}"

    if key not in _active_wyr:
        return await q.answer("Yeh poll expire ho gayi!", show_alert=True)

    data = _active_wyr[key]
    uid = q.from_user.id

    if choice == "a":
        data["votes_b"].discard(uid)
        if uid in data["votes_a"]:
            data["votes_a"].discard(uid)
            await q.answer("Vote hata diya!")
        else:
            data["votes_a"].add(uid)
            await q.answer("🅰️ Option A pe vote diya!")
    else:
        data["votes_a"].discard(uid)
        if uid in data["votes_b"]:
            data["votes_b"].discard(uid)
            await q.answer("Vote hata diya!")
        else:
            data["votes_b"].add(uid)
            await q.answer("🅱️ Option B pe vote diya!")

    va, vb = len(data["votes_a"]), len(data["votes_b"])
    total = va + vb
    pa = int((va / total) * 100) if total else 0
    pb = 100 - pa if total else 0

    try:
        await q.message.edit_reply_markup(InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"🅰️ Option A ({va}) — {pa}%", callback_data=f"wyr_a_{msg_id}"),
                InlineKeyboardButton(f"🅱️ Option B ({vb}) — {pb}%", callback_data=f"wyr_b_{msg_id}"),
            ]
        ]))
    except Exception:
        pass


# ── Riddle ────────────────────────────────────────────────────────────────────

@app.on_message(filters.command(["riddle"]) & filters.group)
async def riddle_cmd(_, m: types.Message):
    question, answer = random.choice(RIDDLES)
    chat_id = m.chat.id
    _active_riddles[chat_id] = {"answer": answer.lower(), "asked_by": m.from_user.id}

    await m.reply_text(
        f"<blockquote><b>🧩 Riddle!</b></blockquote>\n\n"
        f"<blockquote><b>{question}</b>\n\n"
        f"<i>Reply mein jawab do! 60 seconds hain!</i></blockquote>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💡 Hint Chahiye", callback_data=f"riddle_hint_{chat_id}")]
        ])
    )

    await asyncio.sleep(60)
    if chat_id in _active_riddles and _active_riddles[chat_id].get("answer") == answer.lower():
        _active_riddles.pop(chat_id, None)
        try:
            await m.reply_text(
                f"<blockquote><b>⏰ Time Up!</b></blockquote>\n\n"
                f"<blockquote>Jawab tha: <b>{answer}</b></blockquote>"
            )
        except Exception:
            pass


@app.on_callback_query(filters.regex(r"^riddle_hint_(\-?\d+)$"))
async def riddle_hint_cb(_, q: types.CallbackQuery):
    chat_id = int(q.matches[0].group(1))
    if chat_id not in _active_riddles:
        return await q.answer("Riddle khatam ho gayi!", show_alert=True)
    answer = _active_riddles[chat_id]["answer"]
    hint = answer[0] + "*" * (len(answer) - 1)
    await q.answer(f"Hint: {hint}", show_alert=True)


@app.on_message(filters.group & filters.text & ~filters.command([]))
async def riddle_answer_watcher(_, m: types.Message):
    chat_id = m.chat.id
    if chat_id not in _active_riddles:
        return
    data = _active_riddles[chat_id]
    if m.text.strip().lower() == data["answer"]:
        _active_riddles.pop(chat_id, None)
        await m.reply_text(
            f"<blockquote><b>🎉 Sahi Jawab!</b></blockquote>\n\n"
            f"<blockquote>{m.from_user.mention} ne riddle solve kiya!\n"
            f"Jawab: <b>{data['answer'].title()}</b> ✅</blockquote>"
        )


# ── Roast & Compliment ────────────────────────────────────────────────────────

@app.on_message(filters.command(["roast"]) & filters.group)
async def roast_cmd(_, m: types.Message):
    if m.reply_to_message:
        target = m.reply_to_message.from_user
    elif len(m.command) >= 2:
        try:
            target = await app.get_users(m.command[1].lstrip("@"))
        except Exception:
            return await m.reply_text("<blockquote><b>❌ User nahi mila!</b></blockquote>")
    else:
        target = m.from_user

    roast = random.choice(ROASTS)
    await m.reply_text(
        f"<blockquote><b>🔥 Roast Time!</b></blockquote>\n\n"
        f"<blockquote>{target.mention}:\n\n{roast}</blockquote>"
    )


@app.on_message(filters.command(["compliment", "pat"]) & filters.group)
async def compliment_cmd(_, m: types.Message):
    if m.reply_to_message:
        target = m.reply_to_message.from_user
    elif len(m.command) >= 2:
        try:
            target = await app.get_users(m.command[1].lstrip("@"))
        except Exception:
            return await m.reply_text("<blockquote><b>❌ User nahi mila!</b></blockquote>")
    else:
        target = m.from_user

    comp = random.choice(COMPLIMENTS)
    await m.reply_text(
        f"<blockquote><b>💖 Compliment!</b></blockquote>\n\n"
        f"<blockquote>{target.mention}:\n\n{comp}</blockquote>"
    )


# ── 8Ball ─────────────────────────────────────────────────────────────────────

BALL_ANSWERS = [
    "✅ Bilkul haan!", "✅ Pakka!", "✅ Haan, zaroor!",
    "🤔 Shayad...", "🤔 Pata nahi yaar", "🤔 Unclear hai",
    "❌ Nahi bhai nahi", "❌ Bilkul nahi!", "❌ Sapne mein bhi nahi!",
]


@app.on_message(filters.command(["8ball"]) & filters.group)
async def ball_cmd(_, m: types.Message):
    if len(m.command) < 2:
        return await m.reply_text(
            "<blockquote><b>Usage:</b> <code>/8ball aapka sawaal?</code></blockquote>"
        )
    question = " ".join(m.command[1:])
    answer = random.choice(BALL_ANSWERS)
    await m.reply_text(
        f"<blockquote><b>🎱 Magic 8 Ball</b></blockquote>\n\n"
        f"<blockquote>❓ <b>{question}</b>\n\n"
        f"🎱 {answer}</blockquote>"
    )
