import logging
import json
import os
import time
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ChatMemberHandler
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Token ────────────────────────────────────────────────────────────────────
BOT_TOKEN = "8511371551:AAH3J7LFuZv-C9rrwKOCb0K867zN3xPScE0"

# ── Storage ──────────────────────────────────────────────────────────────────
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "warnings": {},
        "messages_total": 0,
        "flood": {},
        "captcha_pending": {},
        "settings": {}
    }

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

data = load_data()

# ── i18n ─────────────────────────────────────────────────────────────────────
TEXTS = {
    "ru": {
        "start": (
            "🛡 *ModBot активен*\n\n"
            "*Команды для админов:*\n"
            "`/warn` — предупреждение (ответом)\n"
            "`/ban` — бан (ответом)\n"
            "`/unban` — разбан (ответом)\n"
            "`/mute 10` — мут на N минут (ответом)\n"
            "`/unmute` — снять мут (ответом)\n"
            "`/warns` — варны юзера (ответом)\n"
            "`/stats` — статистика\n"
            "`/settings` — настройки группы\n\n"
            "*Автомодерация:*\n"
            "🔸 Антиспам\n🔸 Антифлуд\n🔸 Фильтр матов\n🔸 Капча для новых"
        ),
        "admin_only": "❌ Только для администраторов.",
        "reply_needed": "↩️ Ответьте на сообщение пользователя.",
        "warned": "⚠️ {user} получил предупреждение {count}/3\n📝 Причина: {reason}",
        "banned_warns": "🔨 {user} забанен после 3 предупреждений.",
        "banned": "🔨 {user} забанен.\n📝 Причина: {reason}",
        "unbanned": "✅ {user} разбанен.",
        "muted": "🔇 {user} замучен на {mins} мин.",
        "unmuted": "🔊 {user} размучен.",
        "warns_count": "📋 {user}: {count}/3 предупреждений",
        "spam_deleted": "🚫 Сообщение от {user} удалено (спам).",
        "flood_muted": "🌊 {user} замучен за флуд на 5 мин.",
        "profanity_deleted": "🤬 Сообщение от {user} удалено (мат).",
        "auto_banned": "🔨 {user} автоматически забанен.",
        "captcha_msg": "👋 {user}, добро пожаловать!\nДокажи что ты не бот — нажми кнопку ниже в течение 60 сек.",
        "captcha_btn": "✅ Я не бот",
        "captcha_pass": "✅ {user} прошёл капчу!",
        "captcha_fail": "🚫 {user} не прошёл капчу — кик.",
        "stats": "📊 *Статистика*\n\n👥 Участников: {members}\n⚠️ Активных варнов: {warns}\n💬 Сообщений: {msgs}",
        "settings_title": "⚙️ *Настройки группы*",
        "slow_mode_set": "🐢 Медленный режим: {secs} сек.",
        "slow_mode_off": "🐢 Медленный режим отключён.",
    },
    "en": {
        "start": (
            "🛡 *ModBot active*\n\n"
            "*Admin commands:*\n"
            "`/warn` — warn user (reply)\n"
            "`/ban` — ban user (reply)\n"
            "`/unban` — unban user (reply)\n"
            "`/mute 10` — mute for N minutes (reply)\n"
            "`/unmute` — remove mute (reply)\n"
            "`/warns` — user warnings (reply)\n"
            "`/stats` — group statistics\n"
            "`/settings` — group settings\n\n"
            "*Auto-moderation:*\n"
            "🔸 Anti-spam\n🔸 Anti-flood\n🔸 Profanity filter\n🔸 Captcha for new members"
        ),
        "admin_only": "❌ Admins only.",
        "reply_needed": "↩️ Reply to a user message.",
        "warned": "⚠️ {user} warned {count}/3\n📝 Reason: {reason}",
        "banned_warns": "🔨 {user} banned after 3 warnings.",
        "banned": "🔨 {user} banned.\n📝 Reason: {reason}",
        "unbanned": "✅ {user} unbanned.",
        "muted": "🔇 {user} muted for {mins} min.",
        "unmuted": "🔊 {user} unmuted.",
        "warns_count": "📋 {user}: {count}/3 warnings",
        "spam_deleted": "🚫 Message from {user} deleted (spam).",
        "flood_muted": "🌊 {user} muted for flood (5 min).",
        "profanity_deleted": "🤬 Message from {user} deleted (profanity).",
        "auto_banned": "🔨 {user} auto-banned.",
        "captcha_msg": "👋 {user}, welcome!\nProve you're not a bot — press the button within 60 sec.",
        "captcha_btn": "✅ I'm not a bot",
        "captcha_pass": "✅ {user} passed captcha!",
        "captcha_fail": "🚫 {user} failed captcha — kicked.",
        "stats": "📊 *Statistics*\n\n👥 Members: {members}\n⚠️ Active warnings: {warns}\n💬 Messages: {msgs}",
        "settings_title": "⚙️ *Group Settings*",
        "slow_mode_set": "🐢 Slow mode: {secs} sec.",
        "slow_mode_off": "🐢 Slow mode disabled.",
    }
}

PROFANITY = [
    "хуй", "пизда", "блядь", "ебать", "сука", "мудак", "пиздец", "нахуй",
    "fuck", "shit", "bitch", "asshole", "cunt", "dick", "pussy"
]

SPAM_KEYWORDS = ["casino", "crypto", "earn money", "free bitcoin", "click here", "t.me/+"]

# ── Helpers ──────────────────────────────────────────────────────────────────
def t(chat_id: str, key: str, **kwargs):
    lang = data.get("settings", {}).get(chat_id, {}).get("lang", "ru")
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

def get_settings(chat_id: str) -> dict:
    return data.setdefault("settings", {}).setdefault(chat_id, {
        "lang": "ru",
        "profanity_filter": True,
        "antiflood": True,
        "captcha": True,
        "stickers": True,
        "voice": True,
    })

def save_settings(chat_id: str, key: str, value):
    get_settings(chat_id)[key] = value
    save_data(data)

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    return update.effective_user.id in [a.user.id for a in admins]

def get_warn_count(chat_id: str, user_id: str) -> int:
    return data["warnings"].get(chat_id, {}).get(user_id, 0)

def add_warn(chat_id: str, user_id: str) -> int:
    data["warnings"].setdefault(chat_id, {})
    data["warnings"][chat_id][user_id] = data["warnings"][chat_id].get(user_id, 0) + 1
    save_data(data)
    return data["warnings"][chat_id][user_id]

def reset_warns(chat_id: str, user_id: str):
    data["warnings"].get(chat_id, {}).pop(user_id, None)
    save_data(data)

def is_spam(text: str) -> bool:
    if not text:
        return False
    tl = text.lower()
    has_link = any(x in tl for x in ["http://", "https://", "t.me/"])
    has_kw = any(kw in tl for kw in SPAM_KEYWORDS)
    return has_link and has_kw

def has_profanity(text: str) -> bool:
    if not text:
        return False
    tl = text.lower()
    return any(w in tl for w in PROFANITY)

def check_flood(chat_id: str, user_id: str) -> bool:
    key = f"{chat_id}:{user_id}"
    now = time.time()
    flood = data.setdefault("flood", {})
    flood.setdefault(key, [])
    flood[key] = [ts for ts in flood[key] if now - ts < 5]
    flood[key].append(now)
    save_data(data)
    return len(flood[key]) >= 6  # 6 messages in 5 sec = flood

# ── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
    ]])
    await update.message.reply_text(
        "🌐 Выберите язык / Choose language:",
        reply_markup=kb
    )

async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = str(query.message.chat.id)
    lang = query.data.split("_")[1]
    save_settings(chat_id, "lang", lang)
    await query.edit_message_text(
        t(chat_id, "start"),
        parse_mode="Markdown"
    )

# ── /warn ────────────────────────────────────────────────────────────────────
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "reply_needed")); return

    target = update.message.reply_to_message.from_user
    user_id = str(target.id)
    reason = " ".join(context.args) if context.args else ("не указана" if get_settings(chat_id)["lang"] == "ru" else "not specified")
    count = add_warn(chat_id, user_id)

    if count >= 3:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        reset_warns(chat_id, user_id)
        await update.message.reply_text(t(chat_id, "banned_warns", user=target.mention_html()), parse_mode="HTML")
    else:
        await update.message.reply_text(t(chat_id, "warned", user=target.mention_html(), count=count, reason=reason), parse_mode="HTML")

# ── /ban ─────────────────────────────────────────────────────────────────────
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "reply_needed")); return

    target = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else ("не указана" if get_settings(chat_id)["lang"] == "ru" else "not specified")
    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(t(chat_id, "banned", user=target.mention_html(), reason=reason), parse_mode="HTML")

# ── /unban ───────────────────────────────────────────────────────────────────
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "reply_needed")); return

    target = update.message.reply_to_message.from_user
    await context.bot.unban_chat_member(update.effective_chat.id, target.id, only_if_banned=True)
    await update.message.reply_text(t(chat_id, "unbanned", user=target.mention_html()), parse_mode="HTML")

# ── /mute ────────────────────────────────────────────────────────────────────
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "reply_needed")); return

    mins = int(context.args[0]) if context.args and context.args[0].isdigit() else 10
    target = update.message.reply_to_message.from_user
    until = datetime.now() + timedelta(minutes=mins)
    await context.bot.restrict_chat_member(
        update.effective_chat.id, target.id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until
    )
    await update.message.reply_text(t(chat_id, "muted", user=target.mention_html(), mins=mins), parse_mode="HTML")

# ── /unmute ──────────────────────────────────────────────────────────────────
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "reply_needed")); return

    target = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(
        update.effective_chat.id, target.id,
        permissions=ChatPermissions(
            can_send_messages=True, can_send_polls=True,
            can_send_other_messages=True, can_add_web_page_previews=True
        )
    )
    await update.message.reply_text(t(chat_id, "unmuted", user=target.mention_html()), parse_mode="HTML")

# ── /warns ───────────────────────────────────────────────────────────────────
async def check_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "reply_needed")); return
    target = update.message.reply_to_message.from_user
    count = get_warn_count(chat_id, str(target.id))
    await update.message.reply_text(t(chat_id, "warns_count", user=target.mention_html(), count=count), parse_mode="HTML")

# ── /stats ───────────────────────────────────────────────────────────────────
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    members = await context.bot.get_chat_member_count(update.effective_chat.id)
    warns = sum(data["warnings"].get(chat_id, {}).values())
    msgs = data.get("messages_total", 0)
    await update.message.reply_text(t(chat_id, "stats", members=members, warns=warns, msgs=msgs), parse_mode="Markdown")

# ── /settings ────────────────────────────────────────────────────────────────
async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    await send_settings_menu(update.message.chat.id, context, chat_id)

async def send_settings_menu(chat_id_int: int, context: ContextTypes.DEFAULT_TYPE, chat_id: str, message_id=None):
    s = get_settings(chat_id)
    lang = s.get("lang", "ru")

    def toggle(key): return "✅" if s.get(key, True) else "❌"
    label = lambda ru, en: ru if lang == "ru" else en

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🇷🇺 RU / 🇬🇧 EN — {'RU' if lang == 'ru' else 'EN'}", callback_data=f"set_lang_{chat_id}")],
        [InlineKeyboardButton(f"{toggle('profanity_filter')} {label('Фильтр матов', 'Profanity filter')}", callback_data=f"set_profanity_{chat_id}")],
        [InlineKeyboardButton(f"{toggle('antiflood')} {label('Антифлуд', 'Anti-flood')}", callback_data=f"set_flood_{chat_id}")],
        [InlineKeyboardButton(f"{toggle('captcha')} {label('Капча', 'Captcha')}", callback_data=f"set_captcha_{chat_id}")],
        [InlineKeyboardButton(f"{toggle('stickers')} {label('Стикеры', 'Stickers')}", callback_data=f"set_stickers_{chat_id}")],
        [InlineKeyboardButton(f"{toggle('voice')} {label('Голосовые', 'Voice messages')}", callback_data=f"set_voice_{chat_id}")],
        [
            InlineKeyboardButton(label("🐢 Медл. режим", "🐢 Slow mode"), callback_data=f"slowmode_{chat_id}"),
        ],
    ])
    title = t(chat_id, "settings_title")
    if message_id:
        await context.bot.edit_message_text(title, chat_id_int, message_id, parse_mode="Markdown", reply_markup=kb)
    else:
        await context.bot.send_message(chat_id_int, title, parse_mode="Markdown", reply_markup=kb)

async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_str = query.data

    if data_str.startswith("set_lang_"):
        cid = data_str[9:]
        s = get_settings(cid)
        s["lang"] = "en" if s.get("lang", "ru") == "ru" else "ru"
        save_data(data)

    elif data_str.startswith("set_profanity_"):
        cid = data_str[14:]
        s = get_settings(cid)
        s["profanity_filter"] = not s.get("profanity_filter", True)
        save_data(data)

    elif data_str.startswith("set_flood_"):
        cid = data_str[10:]
        s = get_settings(cid)
        s["antiflood"] = not s.get("antiflood", True)
        save_data(data)

    elif data_str.startswith("set_captcha_"):
        cid = data_str[12:]
        s = get_settings(cid)
        s["captcha"] = not s.get("captcha", True)
        save_data(data)

    elif data_str.startswith("set_stickers_"):
        cid = data_str[13:]
        s = get_settings(cid)
        s["stickers"] = not s.get("stickers", True)
        save_data(data)
        # Apply immediately
        perms = await context.bot.get_chat(int(cid))
        allow = s["stickers"]
        await context.bot.set_chat_permissions(int(cid), ChatPermissions(
            can_send_messages=True,
            can_send_other_messages=allow,
            can_send_polls=True,
            can_add_web_page_previews=True
        ))

    elif data_str.startswith("set_voice_"):
        cid = data_str[10:]
        s = get_settings(cid)
        s["voice"] = not s.get("voice", True)
        save_data(data)

    elif data_str.startswith("slowmode_"):
        cid = data_str[9:]
        lang = get_settings(cid).get("lang", "ru")
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("Off", callback_data=f"sm_0_{cid}"),
            InlineKeyboardButton("10s", callback_data=f"sm_10_{cid}"),
            InlineKeyboardButton("30s", callback_data=f"sm_30_{cid}"),
            InlineKeyboardButton("1m", callback_data=f"sm_60_{cid}"),
            InlineKeyboardButton("5m", callback_data=f"sm_300_{cid}"),
        ]])
        await query.edit_message_reply_markup(reply_markup=kb)
        return

    elif data_str.startswith("sm_"):
        parts = data_str.split("_")
        secs = int(parts[1])
        cid = "_".join(parts[2:])
        await context.bot.set_chat_slow_mode_delay(int(cid), secs)
        msg = t(cid, "slow_mode_set", secs=secs) if secs > 0 else t(cid, "slow_mode_off")
        await query.answer(msg, show_alert=True)

    if "_" in data_str:
        parts = data_str.split("_")
        cid = parts[-1]
        try:
            await send_settings_menu(int(cid), context, cid, query.message.message_id)
        except Exception:
            pass

# ── Captcha ───────────────────────────────────────────────────────────────────
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        chat_id = str(update.effective_chat.id)
        if not get_settings(chat_id).get("captcha", True):
            continue

        # Mute until captcha passed
        await context.bot.restrict_chat_member(
            update.effective_chat.id, member.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(t(chat_id, "captcha_btn"), callback_data=f"captcha_{member.id}_{chat_id}")
        ]])
        msg = await context.bot.send_message(
            update.effective_chat.id,
            t(chat_id, "captcha_msg", user=member.mention_html()),
            parse_mode="HTML",
            reply_markup=kb
        )
        # Schedule kick after 60 sec
        context.job_queue.run_once(
            kick_if_no_captcha,
            60,
            data={"chat_id": update.effective_chat.id, "user_id": member.id, "msg_id": msg.message_id, "chat_id_str": chat_id},
            name=f"captcha_{member.id}_{chat_id}"
        )
        data.setdefault("captcha_pending", {})[f"{chat_id}:{member.id}"] = True
        save_data(data)

async def kick_if_no_captcha(context: ContextTypes.DEFAULT_TYPE):
    d = context.job.data
    key = f"{d['chat_id_str']}:{d['user_id']}"
    if data.get("captcha_pending", {}).get(key):
        try:
            await context.bot.ban_chat_member(d["chat_id"], d["user_id"])
            await context.bot.unban_chat_member(d["chat_id"], d["user_id"])
            await context.bot.delete_message(d["chat_id"], d["msg_id"])
        except Exception as e:
            logger.error(f"Captcha kick error: {e}")
        data["captcha_pending"].pop(key, None)
        save_data(data)

async def captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split("_")
    user_id = int(parts[1])
    chat_id_str = parts[2]

    if query.from_user.id != user_id:
        await query.answer("❌")
        return

    await query.answer("✅")
    key = f"{chat_id_str}:{user_id}"
    data.get("captcha_pending", {}).pop(key, None)
    save_data(data)

    # Restore permissions
    await context.bot.restrict_chat_member(
        int(chat_id_str), user_id,
        permissions=ChatPermissions(
            can_send_messages=True, can_send_polls=True,
            can_send_other_messages=True, can_add_web_page_previews=True
        )
    )
    await query.edit_message_text(t(chat_id_str, "captcha_pass", user=query.from_user.mention_html()), parse_mode="HTML")

# ── Auto-moderation ──────────────────────────────────────────────────────────
async def auto_moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    user_id = str(user.id)
    s = get_settings(chat_id)

    data["messages_total"] = data.get("messages_total", 0) + 1
    save_data(data)

    # Voice filter
    if update.message.voice and not s.get("voice", True):
        try:
            await update.message.delete()
        except Exception:
            pass
        return

    # Sticker filter
    if update.message.sticker and not s.get("stickers", True):
        try:
            await update.message.delete()
        except Exception:
            pass
        return

    text = update.message.text or update.message.caption or ""

    # Spam check
    if is_spam(text):
        try:
            await update.message.delete()
            await context.bot.send_message(update.effective_chat.id, t(chat_id, "spam_deleted", user=user.mention_html()), parse_mode="HTML")
            count = add_warn(chat_id, user_id)
            if count >= 3:
                await context.bot.ban_chat_member(update.effective_chat.id, user.id)
                reset_warns(chat_id, user_id)
                await context.bot.send_message(update.effective_chat.id, t(chat_id, "auto_banned", user=user.mention_html()), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Spam mod error: {e}")
        return

    # Profanity check
    if s.get("profanity_filter", True) and has_profanity(text):
        try:
            await update.message.delete()
            await context.bot.send_message(update.effective_chat.id, t(chat_id, "profanity_deleted", user=user.mention_html()), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Profanity mod error: {e}")
        return

    # Flood check
    if s.get("antiflood", True) and check_flood(chat_id, user_id):
        try:
            until = datetime.now() + timedelta(minutes=5)
            await context.bot.restrict_chat_member(
                update.effective_chat.id, user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until
            )
            await context.bot.send_message(update.effective_chat.id, t(chat_id, "flood_muted", user=user.mention_html()), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Flood mod error: {e}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("warn", warn_user))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("warns", check_warns))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("settings", settings_cmd))

    app.add_handler(CallbackQueryHandler(lang_callback, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(captcha_callback, pattern="^captcha_"))
    app.add_handler(CallbackQueryHandler(settings_callback, pattern="^(set_|slowmode_|sm_)"))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, auto_moderate))

    logger.info("ModBot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
