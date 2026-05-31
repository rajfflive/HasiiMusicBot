# 🎵 HasiiMusicBot

> Advanced Telegram Music Bot with YouTube streaming, live radio, and studio-quality audio playback in voice chats.  
> Built with **Python**, **Pyrogram** & **PyTgCalls** — now with full **GIF Manager** support!

---

## 🎬 GIF Manager — Bot Se Seedha GIF Change Karo!

Har feature ke liye apna custom GIF set kar sakte ho — directly Telegram bot se, bina code touch kiye.  
GIFs **MongoDB** mein save hote hain — bot restart ke baad bhi rehte hain.

---

### 🟢 Start GIF
Jab koi `/start` kare private chat mein — yeh GIF aayega.

| Command | Kaam |
|---|---|
| `/setstartgif` | GIF reply karke send karo → add ho jaayega |
| `/setstartgif naam` | GIF reply + custom naam |
| `/rmstartgif <n>` | Number wali GIF remove karo |
| `/liststartgif` | Saari start GIFs dekho |

---

### 👋 Welcome GIF
Jab koi naya member group join kare — yeh GIF welcome ke saath aayega.

| Command | Kaam |
|---|---|
| `/setwelgif` | Welcome GIF add karo |
| `/rmwelgif <n>` | Remove |
| `/listwelgif` | List |

**Welcome message bhi customize karo:**
```
/setwel Namaste {mention}! {chat_title} mein aapka swagat hai 🎉
```
**Placeholders:** `{mention}` `{first_name}` `{username}` `{chat_title}` `{id}`

**Welcome on/off:**
```
/startwel   → Enable
/stopwel    → Disable
/resetwel   → Default pe wapas
/welshow    → Current settings dekho
```

---

### 💑 Couple GIF
`/couple` aur `/couples` commands pe yeh GIF aayega.

| Command | Kaam |
|---|---|
| `/setcouplegif` | Couple GIF add karo |
| `/rmcouplegif <n>` | Remove |
| `/listcouplegif` | List |

**Couple Commands:**
```
/couple @user     → Kisi se couple bano
/uncouple         → Breakup karo
/mycouple         → Apna couple status dekho
/couples          → Random couple from group
/couplerank       → Top couples list
```

---

### 😴 AFK GIF
`/afk` karte waqt yeh GIF aayega.

| Command | Kaam |
|---|---|
| `/setafkgif` | AFK GIF add karo |
| `/rmafkgif <n>` | Remove |
| `/listafkgif` | List |

**AFK Commands:**
```
/afk [reason]   → AFK mode on (GIF ke saath)
/back           → Manually wapas aao
```
> Auto-return bhi hota hai jab tum kuch message karo!  
> Agar koi tumhe mention kare aur tum AFK ho — bot automatically batata hai.

---

### 🎵 Play GIF / Sticker
`/play` command chalane pe yeh sticker/GIF aayega processing indicator ke taur par.  
**Ab hardcoded nahi — bot se seedha change karo!**

| Command | Kaam |
|---|---|
| `/setplaygif` | Play sticker/GIF add karo (reply karke) |
| `/rmplaygif <n>` | Remove |
| `/listplaygif` | List |

> Sticker aur GIF dono support karta hai!

---

### 🏷️ TagAll Greeting GIFs
Har greeting command ke saath apna alag GIF set karo.

| GIF Type | Set Command | Tag Command |
|---|---|---|
| Good Morning 🌅 | `/setgmgif` | `/gmtag [msg]` |
| Good Night 🌙 | `/setgngif` | `/gntag [msg]` |
| Good Afternoon ☀️ | `/setgdgif` | `/gdtag [msg]` |
| Good Evening 🌆 | `/setgevgif` | `/gevtag [msg]` |
| Birthday 🎂 | `/setgbdgif` | `/gbdtag @user` |

**List / Remove (example for Good Morning):**
```
/listgmgif        → List dekho
/rmgmgif <n>      → Remove karo
```

**Other TagAll Commands:**
```
/tagall [msg]       → Sab members tag karo
/tagadmins [msg]    → Sirf admins tag
/stoptag            → Tag rokdo
```

---

## 🎬 GIF Set Karne Ka Tarika

1. **Bot mein koi GIF ya Sticker bhejo** (group ya private dono mein kaam karta hai)
2. **Usi GIF ko reply karo** aur command likho:

```
/setplaygif             ← play ke liye
/setafkgif meri-gif     ← afk ke liye (custom naam ke saath)
/setcouplegif           ← couple ke liye
```

3. Done! ✅ Ab se wahi GIF use hoga.

> **Permission:** Sirf **Owner / Sudo / Group Admin** GIF set/remove kar sakta hai.

---

## 🎵 Music Commands

```
/play <song name or URL>   → Song bajao
/vplay <song>              → Video play karo
/cplay <song>              → Linked channel mein play
/pause                     → Pause
/resume                    → Resume
/skip                      → Agla song
/stop                      → Band karo
/queue                     → Queue dekho
/loop                      → Loop toggle (off → single → queue)
/shuffle                   → Queue shuffle karo
/seek <seconds>            → Seek karo
```

---

## ⚙️ Admin Controls

```
/auth @user        → User ko music commands use karne do (non-admin)
/unauth @user      → Permission hatao
/authlist          → Authorized users list
/playmode          → Play mode toggle (admin only / everyone)
/channelplay       → Channel play enable/disable
```

---

## 🛡️ Sudo / Owner Commands

```
/broadcast <msg>   → Sab groups mein message bhejo
/gban @user        → Global ban
/ungban @user      → Global unban
/sudolist          → Sudo users list
/maintenance       → Maintenance mode
/restart           → Bot restart
```

---

## 🚀 Setup

### Requirements
```
Python 3.10+
MongoDB
FFmpeg
```

### Install
```bash
git clone https://github.com/rajfflive/HasiiMusicBot
cd HasiiMusicBot
pip install -r requirements.txt
```

### Config (`config.py` ya Environment Variables)
```env
API_ID         = your_api_id
API_HASH       = your_api_hash
BOT_TOKEN      = your_bot_token
OWNER_ID       = your_telegram_id
MONGO_DB_URI   = mongodb://...
STRING_SESSION = your_string_session
SUPPORT_CHAT   = @your_support_group
```

### Run
```bash
python -m HasiiMusic
```

---

## 📁 Project Structure

```
HasiiMusic/
├── core/           → Bot, Calls, MongoDB, YouTube, Telegram core
├── helpers/
│   ├── gif_manager.py   ← GIF Manager (saari GIF logic yahan)
│   └── ...
├── plugins/
│   ├── features/
│   │   ├── afk.py       ← AFK + GIF
│   │   ├── couple.py    ← Couple + GIF
│   │   └── tagall.py    ← TagAll + Greeting GIFs
│   ├── events/
│   │   └── welcome.py   ← Welcome + GIF
│   ├── information/
│   │   └── start.py     ← Start + GIF
│   └── playback-controls/
│       └── play.py      ← Play + GIF/Sticker
└── locales/        → Language files
```

---

## 🤝 Credits

- Original base: [AnonXMusic](https://github.com/AnonymousX1025/AnonXMusic)
- Customized by: [@rajfflive](https://github.com/rajfflive)
- GIF Manager system added for full bot-side GIF control

---

## 📜 License

MIT License — Free to use and modify.
