import logging
import json
import os
import time
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, PrefixHandler
)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8511371551:AAH3J7LFuZv-C9rrwKOCb0K867zN3xPScE0"
DATA_FILE = "data.json"

# ── Storage ───────────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"warnings": {}, "messages_total": 0, "flood": {}, "captcha_pending": {}, "settings": {}, "spam_history": {}}

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

data = load_data()

# ── i18n ──────────────────────────────────────────────────────────────────────
TEXTS = {
    "ru": {
        "start": (
            "🛡 *ModBot активен*\n\n"
            "*Команды для админов (префикс !):*\n"
            "`!warn` — предупреждение (ответом)\n"
            "`!ban` — бан (ответом)\n"
            "`!unban` — разбан (ответом)\n"
            "`!mute 10` — мут на N минут (ответом)\n"
            "`!unmute` — снять мут (ответом)\n"
            "`!warns` — варны юзера (ответом)\n"
            "`!stats` — статистика\n"
            "`!addword слово` — добавить слово в фильтр\n"
            "`!delword слово` — удалить слово\n"
            "`!words` — список слов фильтра\n"
            "`!settings` — настройки группы\n\n"
            "*Автомодерация:*\n"
            "🔸 Антиспам (дубли ссылок = мут)\n🔸 Антифлуд\n🔸 Фильтр слов\n🔸 Капча для новых"
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
        "spam_deleted": "🚫 Спам от {user} удалён.",
        "spam_dup_muted": "🚫 {user} замучен на {mins} мин. за повторную ссылку.",
        "flood_muted": "🌊 {user} замучен за флуд на {mins} мин.",
        "word_deleted": "🤬 Сообщение от {user} удалено (запрещённое слово). Мут {mins} мин.",
        "auto_banned": "🔨 {user} автоматически забанен.",
        "captcha_msg": "👋 {user}, добро пожаловать!\nДокажи что ты не бот — нажми кнопку ниже в течение 60 сек.",
        "captcha_btn": "✅ Я не бот",
        "captcha_pass": "✅ {user} прошёл капчу!",
        "captcha_fail": "⏰ {user} не прошёл капчу — кик.",
        "stats": "📊 *Статистика*\n\n👥 Участников: {members}\n⚠️ Активных варнов: {warns}\n💬 Сообщений: {msgs}",
        "settings_title": "⚙️ *Настройки группы*\n_(только для администраторов)_",
        "word_added": "✅ Слово добавлено: `{word}`",
        "word_removed": "✅ Слово удалено: `{word}`",
        "word_not_found": "❌ Слово не найдено в фильтре.",
        "words_list": "📋 *Слова фильтра:*\n{words}",
        "words_empty": "📋 Фильтр слов пуст.",
    },
    "en": {
        "start": (
            "🛡 *ModBot active*\n\n"
            "*Admin commands (prefix !):*\n"
            "`!warn` — warn user (reply)\n"
            "`!ban` — ban user (reply)\n"
            "`!unban` — unban user (reply)\n"
            "`!mute 10` — mute N minutes (reply)\n"
            "`!unmute` — remove mute (reply)\n"
            "`!warns` — user warnings (reply)\n"
            "`!stats` — group statistics\n"
            "`!addword word` — add word to filter\n"
            "`!delword word` — remove word\n"
            "`!words` — list filtered words\n"
            "`!settings` — group settings\n\n"
            "*Auto-moderation:*\n"
            "🔸 Anti-spam (duplicate links = mute)\n🔸 Anti-flood\n🔸 Word filter\n🔸 Captcha for new members"
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
        "spam_deleted": "🚫 Spam from {user} deleted.",
        "spam_dup_muted": "🚫 {user} muted {mins} min. for duplicate link.",
        "flood_muted": "🌊 {user} muted for flood ({mins} min).",
        "word_deleted": "🤬 Message from {user} deleted (banned word). Muted {mins} min.",
        "auto_banned": "🔨 {user} auto-banned.",
        "captcha_msg": "👋 {user}, welcome!\nProve you're not a bot — press the button within 60 sec.",
        "captcha_btn": "✅ I'm not a bot",
        "captcha_pass": "✅ {user} passed captcha!",
        "captcha_fail": "⏰ {user} failed captcha — kicked.",
        "stats": "📊 *Statistics*\n\n👥 Members: {members}\n⚠️ Active warnings: {warns}\n💬 Messages: {msgs}",
        "settings_title": "⚙️ *Group Settings*\n_(admins only)_",
        "word_added": "✅ Word added: `{word}`",
        "word_removed": "✅ Word removed: `{word}`",
        "word_not_found": "❌ Word not found in filter.",
        "words_list": "📋 *Filtered words:*\n{words}",
        "words_empty": "📋 Word filter is empty.",
    }
}

SPAM_KEYWORDS = ["casino", "crypto", "earn money", "free bitcoin", "click here", "t.me/+"]

# ── Helpers ───────────────────────────────────────────────────────────────────
def t(chat_id: str, key: str, **kwargs):
    lang = data.get("settings", {}).get(chat_id, {}).get("lang", "ru")
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

def get_settings(chat_id: str) -> dict:
    s = data.setdefault("settings", {})
    if chat_id not in s:
        s[chat_id] = {
            "lang": "ru", "profanity_filter": True, "antiflood": True,
            "captcha": True, "mute_spam": 20, "mute_flood": 5, "mute_words": 10,
            "custom_words": []
        }
    return s[chat_id]

async def get_admin_ids(context, chat_id_int: int) -> list:
    try:
        admins = await context.bot.get_chat_administrators(chat_id_int)
        return [a.user.id for a in admins]
    except:
        return []

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    admin_ids = await get_admin_ids(context, update.effective_chat.id)
    return update.effective_user.id in admin_ids

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

def extract_links(text: str) -> list:
    import re
    return re.findall(r'https?://\S+|t\.me/\S+', text.lower())

def is_spam(text: str) -> bool:
    if not text: return False
    tl = text.lower()
    has_link = any(x in tl for x in ["http://", "https://", "t.me/"])
    has_kw = any(kw in tl for kw in SPAM_KEYWORDS)
    return has_link and has_kw

def check_duplicate_link(chat_id: str, user_id: str, text: str) -> bool:
    links = extract_links(text)
    if not links: return False
    key = f"{chat_id}:{user_id}"
    now = time.time()
    history = data.setdefault("spam_history", {})
    history.setdefault(key, [])
    history[key] = [e for e in history[key] if now - e["ts"] < 60]
    for link in links:
        for entry in history[key]:
            if entry["link"] == link:
                save_data(data)
                return True
    for link in links:
        history[key].append({"link": link, "ts": now})
    save_data(data)
    return False

def has_banned_word(chat_id: str, text: str) -> bool:
    if not text: return False
    tl = text.lower()
    words = get_settings(chat_id).get("custom_words", [])
    return any(w in tl for w in words)

def check_flood(chat_id: str, user_id: str) -> bool:
    key = f"{chat_id}:{user_id}"
    now = time.time()
    flood = data.setdefault("flood", {})
    flood.setdefault(key, [])
    flood[key] = [ts for ts in flood[key] if now - ts < 5]
    flood[key].append(now)
    save_data(data)
    return len(flood[key]) >= 6

async def do_mute(context, chat_id_int: int, user_id: int, mins: int):
    until = datetime.now() + timedelta(minutes=mins)
    await context.bot.restrict_chat_member(
        chat_id_int, user_id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until
    )

# ── /start ────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
    ]])
    await update.message.reply_text("🌐 Выберите язык / Choose language:", reply_markup=kb)

async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat.id)
    # Only admins can change language
    admin_ids = await get_admin_ids(context, query.message.chat.id)
    if query.from_user.id not in admin_ids:
        await query.answer("❌ Только для администраторов.", show_alert=True)
        return
    await query.answer()
    lang = query.data.split("_")[1]
    get_settings(chat_id)["lang"] = lang
    save_data(data)
    await query.edit_message_text(t(chat_id, "start"), parse_mode="Markdown")

# ── !warn ─────────────────────────────────────────────────────────────────────
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "reply_needed")); return
    target = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "—"
    count = add_warn(chat_id, str(target.id))
    if count >= 3:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        reset_warns(chat_id, str(target.id))
        await update.message.reply_text(t(chat_id, "banned_warns", user=target.mention_html()), parse_mode="HTML")
    else:
        await update.message.reply_text(t(chat_id, "warned", user=target.mention_html(), count=count, reason=reason), parse_mode="HTML")

# ── !ban ──────────────────────────────────────────────────────────────────────
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "reply_needed")); return
    target = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "—"
    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(t(chat_id, "banned", user=target.mention_html(), reason=reason), parse_mode="HTML")

# ── !unban ────────────────────────────────────────────────────────────────────
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "reply_needed")); return
    target = update.message.reply_to_message.from_user
    await context.bot.unban_chat_member(update.effective_chat.id, target.id, only_if_banned=True)
    await update.message.reply_text(t(chat_id, "unbanned", user=target.mention_html()), parse_mode="HTML")

# ── !mute ─────────────────────────────────────────────────────────────────────
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "reply_needed")); return
    mins = int(context.args[0]) if context.args and context.args[0].isdigit() else 10
    target = update.message.reply_to_message.from_user
    await do_mute(context, update.effective_chat.id, target.id, mins)
    await update.message.reply_text(t(chat_id, "muted", user=target.mention_html(), mins=mins), parse_mode="HTML")

# ── !unmute ───────────────────────────────────────────────────────────────────
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

# ── !warns ────────────────────────────────────────────────────────────────────
async def check_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not update.message.reply_to_message:
        await update.message.reply_text(t(chat_id, "reply_needed")); return
    target = update.message.reply_to_message.from_user
    count = get_warn_count(chat_id, str(target.id))
    await update.message.reply_text(t(chat_id, "warns_count", user=target.mention_html(), count=count), parse_mode="HTML")

# ── !stats ────────────────────────────────────────────────────────────────────
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    members = await context.bot.get_chat_member_count(update.effective_chat.id)
    warns = sum(data["warnings"].get(chat_id, {}).values())
    msgs = data.get("messages_total", 0)
    await update.message.reply_text(t(chat_id, "stats", members=members, warns=warns, msgs=msgs), parse_mode="Markdown")

# ── !addword / !delword / !words ──────────────────────────────────────────────
async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    if not context.args:
        await update.message.reply_text("Использование: !addword слово"); return
    word = " ".join(context.args).lower().strip()
    words = get_settings(chat_id).setdefault("custom_words", [])
    if word not in words:
        words.append(word)
        save_data(data)
    await update.message.reply_text(t(chat_id, "word_added", word=word), parse_mode="Markdown")

async def del_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    if not context.args:
        await update.message.reply_text("Использование: !delword слово"); return
    word = " ".join(context.args).lower().strip()
    words = get_settings(chat_id).get("custom_words", [])
    if word in words:
        words.remove(word)
        save_data(data)
        await update.message.reply_text(t(chat_id, "word_removed", word=word), parse_mode="Markdown")
    else:
        await update.message.reply_text(t(chat_id, "word_not_found"))

async def list_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    words = get_settings(chat_id).get("custom_words", [])
    if not words:
        await update.message.reply_text(t(chat_id, "words_empty")); return
    await update.message.reply_text(t(chat_id, "words_list", words="\n".join(f"• `{w}`" for w in words)), parse_mode="Markdown")

# ── !settings ─────────────────────────────────────────────────────────────────
async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not await is_admin(update, context):
        await update.message.reply_text(t(chat_id, "admin_only")); return
    await send_settings_menu(update.effective_chat.id, context, chat_id)

async def send_settings_menu(chat_id_int: int, context, chat_id: str, message_id=None):
    s = get_settings(chat_id)
    lang = s.get("lang", "ru")
    def on(key): return "✅" if s.get(key, True) else "❌"
    L = lambda ru, en: ru if lang == "ru" else en

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🌐 {L('Язык','Language')}: {'RU' if lang=='ru' else 'EN'}", callback_data=f"set_lang_{chat_id}")],
        [InlineKeyboardButton(f"{on('profanity_filter')} {L('Фильтр слов','Word filter')}", callback_data=f"set_profanity_{chat_id}")],
        [InlineKeyboardButton(f"{on('antiflood')} {L('Антифлуд','Anti-flood')}", callback_data=f"set_flood_{chat_id}")],
        [InlineKeyboardButton(f"{on('captcha')} {L('Капча','Captcha')}", callback_data=f"set_captcha_{chat_id}")],
        [
            InlineKeyboardButton(f"⏱ {L('Спам','Spam')}: {s.get('mute_spam',20)}м", callback_data=f"mutecfg_spam_{chat_id}"),
            InlineKeyboardButton(f"⏱ {L('Флуд','Flood')}: {s.get('mute_flood',5)}м", callback_data=f"mutecfg_flood_{chat_id}"),
            InlineKeyboardButton(f"⏱ {L('Слова','Words')}: {s.get('mute_words',10)}м", callback_data=f"mutecfg_words_{chat_id}"),
        ],
    ])
    title = t(chat_id, "settings_title")
    try:
        if message_id:
            await context.bot.edit_message_text(title, chat_id_int, message_id, parse_mode="Markdown", reply_markup=kb)
        else:
            await context.bot.send_message(chat_id_int, title, parse_mode="Markdown", reply_markup=kb)
    except Exception as e:
        logger.error(f"Settings menu error: {e}")

async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    d = query.data

    # Extract chat_id from callback data
    # Format: prefix_chatid  or  prefix_type_chatid
    # We need to check admin rights using the chat where settings were opened
    # The message is in the group, so use query.message.chat.id
    chat_id_int = query.message.chat.id
    admin_ids = await get_admin_ids(context, chat_id_int)
    if query.from_user.id not in admin_ids:
        await query.answer("❌ Только для администраторов.", show_alert=True)
        return

    await query.answer()
    cid = None

    if d.startswith("set_lang_"):
        cid = d[9:]; s = get_settings(cid); s["lang"] = "en" if s.get("lang","ru")=="ru" else "ru"; save_data(data)
    elif d.startswith("set_profanity_"):
        cid = d[14:]; s = get_settings(cid); s["profanity_filter"] = not s.get("profanity_filter", True); save_data(data)
    elif d.startswith("set_flood_"):
        cid = d[10:]; s = get_settings(cid); s["antiflood"] = not s.get("antiflood", True); save_data(data)
    elif d.startswith("set_captcha_"):
        cid = d[12:]; s = get_settings(cid); s["captcha"] = not s.get("captcha", True); save_data(data)

    elif d.startswith("mutecfg_"):
        parts = d.split("_"); mtype = parts[1]; cid = "_".join(parts[2:])
        options = [1, 5, 10, 20, 30, 60]
        current = get_settings(cid).get(f"mute_{mtype}", 10)
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"{'▶' if o==current else ''}{o}м", callback_data=f"setmute_{mtype}_{o}_{cid}")
            for o in options
        ]])
        await query.edit_message_reply_markup(reply_markup=kb)
        return

    elif d.startswith("setmute_"):
        parts = d.split("_"); mtype = parts[1]; mins = int(parts[2]); cid = "_".join(parts[3:])
        get_settings(cid)[f"mute_{mtype}"] = mins; save_data(data)

    if cid:
        try:
            await send_settings_menu(int(cid), context, cid, query.message.message_id)
        except Exception as e:
            logger.error(f"Settings update error: {e}")

# ── Captcha ───────────────────────────────────────────────────────────────────
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        chat_id = str(update.effective_chat.id)
        if not get_settings(chat_id).get("captcha", True):
            continue
        try:
            # Restrict new member from sending messages
            await context.bot.restrict_chat_member(
                update.effective_chat.id,
                member.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                )
            )
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    t(chat_id, "captcha_btn"),
                    callback_data=f"captcha_{member.id}_{chat_id}"
                )
            ]])
            msg = await context.bot.send_message(
                update.effective_chat.id,
                t(chat_id, "captcha_msg", user=member.mention_html()),
                parse_mode="HTML",
                reply_markup=kb
            )
            # Store pending
            data.setdefault("captcha_pending", {})[f"{chat_id}:{member.id}"] = {
                "msg_id": msg.message_id,
                "ts": time.time()
            }
            save_data(data)
            # Schedule kick after 60 sec
            context.job_queue.run_once(
                kick_if_no_captcha, 60,
                data={"chat_id_int": update.effective_chat.id, "user_id": member.id, "msg_id": msg.message_id, "chat_id_str": chat_id},
                name=f"cap_{member.id}_{chat_id}"
            )
        except Exception as e:
            logger.error(f"Captcha setup error: {e}")

async def kick_if_no_captcha(context: ContextTypes.DEFAULT_TYPE):
    d = context.job.data
    key = f"{d['chat_id_str']}:{d['user_id']}"
    pending = data.get("captcha_pending", {})
    if key in pending:
        try:
            # Kick (ban + unban = kick)
            await context.bot.ban_chat_member(d["chat_id_int"], d["user_id"])
            await context.bot.unban_chat_member(d["chat_id_int"], d["user_id"])
            try:
                await context.bot.delete_message(d["chat_id_int"], d["msg_id"])
            except:
                pass
            await context.bot.send_message(
                d["chat_id_int"],
                t(d["chat_id_str"], "captcha_fail", user=f"#{d['user_id']}"),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Captcha kick error: {e}")
        pending.pop(key, None)
        save_data(data)

async def captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split("_")
    # Format: captcha_USERID_CHATID (chatid can have minus sign)
    user_id = int(parts[1])
    chat_id_str = "_".join(parts[2:])

    # Only the invited user can press the button
    if query.from_user.id != user_id:
        await query.answer("❌ Эта кнопка не для тебя.", show_alert=True)
        return

    key = f"{chat_id_str}:{user_id}"
    pending = data.get("captcha_pending", {})

    if key not in pending:
        await query.answer("✅ Уже подтверждено.")
        return

    await query.answer("✅ Проверка пройдена!")
    pending.pop(key, None)
    save_data(data)

    try:
        # Restore full permissions
        await context.bot.restrict_chat_member(
            int(chat_id_str), user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
        )
        await query.edit_message_text(
            t(chat_id_str, "captcha_pass", user=query.from_user.mention_html()),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Captcha pass error: {e}")

# ── Auto-moderation ───────────────────────────────────────────────────────────
async def auto_moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    if not user:
        return
    user_id = str(user.id)
    s = get_settings(chat_id)

    data["messages_total"] = data.get("messages_total", 0) + 1

    # Admins bypass all filters
    admin_ids = await get_admin_ids(context, update.effective_chat.id)
    if user.id in admin_ids:
        save_data(data)
        return

    text = update.message.text or update.message.caption or ""

    # Duplicate link check → immediate mute
    if check_duplicate_link(chat_id, user_id, text):
        mins = s.get("mute_spam", 20)
        try:
            await update.message.delete()
            await do_mute(context, update.effective_chat.id, user.id, mins)
            await context.bot.send_message(
                update.effective_chat.id,
                t(chat_id, "spam_dup_muted", user=user.mention_html(), mins=mins),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Dup link error: {e}")
        save_data(data)
        return

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
            logger.error(f"Spam error: {e}")
        save_data(data)
        return

    # Word filter
    if s.get("profanity_filter", True) and has_banned_word(chat_id, text):
        mins = s.get("mute_words", 10)
        try:
            await update.message.delete()
            await do_mute(context, update.effective_chat.id, user.id, mins)
            await context.bot.send_message(update.effective_chat.id, t(chat_id, "word_deleted", user=user.mention_html(), mins=mins), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Word filter error: {e}")
        save_data(data)
        return

    # Flood check
    if s.get("antiflood", True) and check_flood(chat_id, user_id):
        mins = s.get("mute_flood", 5)
        try:
            await do_mute(context, update.effective_chat.id, user.id, mins)
            await context.bot.send_message(update.effective_chat.id, t(chat_id, "flood_muted", user=user.mention_html(), mins=mins), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Flood error: {e}")

    save_data(data)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(PrefixHandler("!", "start", start))
    app.add_handler(PrefixHandler("!", "warn", warn_user))
    app.add_handler(PrefixHandler("!", "ban", ban_user))
    app.add_handler(PrefixHandler("!", "unban", unban_user))
    app.add_handler(PrefixHandler("!", "mute", mute_user))
    app.add_handler(PrefixHandler("!", "unmute", unmute_user))
    app.add_handler(PrefixHandler("!", "warns", check_warns))
    app.add_handler(PrefixHandler("!", "stats", stats))
    app.add_handler(PrefixHandler("!", "settings", settings_cmd))
    app.add_handler(PrefixHandler("!", "addword", add_word))
    app.add_handler(PrefixHandler("!", "delword", del_word))
    app.add_handler(PrefixHandler("!", "words", list_words))
    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(lang_callback, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(captcha_callback, pattern="^captcha_"))
    app.add_handler(CallbackQueryHandler(settings_callback, pattern="^(set_|mutecfg_|setmute_)"))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, auto_moderate))

    logger.info("ModBot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
