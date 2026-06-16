import logging
import json
import os
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Storage (simple JSON file) ──────────────────────────────────────────────
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"warnings": {}, "banned": [], "joins": {}, "messages_total": 0}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

# ── Spam detection ──────────────────────────────────────────────────────────
SPAM_KEYWORDS = ["casino", "crypto", "earn money", "free bitcoin", "click here", "t.me/+"]

def is_spam(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    has_link = "http://" in text_lower or "https://" in text_lower or "t.me/" in text_lower
    has_keyword = any(kw in text_lower for kw in SPAM_KEYWORDS)
    return has_link and has_keyword

# ── Helpers ─────────────────────────────────────────────────────────────────
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    admin_ids = [a.user.id for a in admins]
    return update.effective_user.id in admin_ids

def get_warn_count(chat_id: str, user_id: str) -> int:
    return data["warnings"].get(chat_id, {}).get(user_id, 0)

def add_warn(chat_id: str, user_id: str) -> int:
    data["warnings"].setdefault(chat_id, {})
    data["warnings"][chat_id][user_id] = data["warnings"][chat_id].get(user_id, 0) + 1
    save_data(data)
    return data["warnings"][chat_id][user_id]

def reset_warns(chat_id: str, user_id: str):
    if chat_id in data["warnings"]:
        data["warnings"][chat_id].pop(user_id, None)
    save_data(data)

# ── Commands ─────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡 *ModBot активен*\n\n"
        "Команды для админов:\n"
        "`/warn @user` — выдать предупреждение\n"
        "`/ban @user` — забанить\n"
        "`/unban @user` — разбанить\n"
        "`/stats` — статистика группы\n"
        "`/warns @user` — сколько варнов у юзера",
        parse_mode="Markdown"
    )

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только для администраторов.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ Ответьте на сообщение пользователя командой /warn")
        return

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    user_id = str(target.id)

    count = add_warn(chat_id, user_id)
    reason = " ".join(context.args) if context.args else "не указана"

    if count >= 3:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        reset_warns(chat_id, user_id)
        await update.message.reply_text(
            f"🔨 {target.mention_html()} забанен после 3 предупреждений.",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            f"⚠️ {target.mention_html()} получил предупреждение {count}/3\n"
            f"📝 Причина: {reason}",
            parse_mode="HTML"
        )

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только для администраторов.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ Ответьте на сообщение пользователя командой /ban")
        return

    target = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "не указана"

    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(
        f"🔨 {target.mention_html()} забанен.\n📝 Причина: {reason}",
        parse_mode="HTML"
    )

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Только для администраторов.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ Ответьте на сообщение пользователя командой /unban")
        return

    target = update.message.reply_to_message.from_user
    await context.bot.unban_chat_member(update.effective_chat.id, target.id, only_if_banned=True)
    await update.message.reply_text(
        f"✅ {target.mention_html()} разбанен.",
        parse_mode="HTML"
    )

async def check_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ Ответьте на сообщение пользователя командой /warns")
        return

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    user_id = str(target.id)
    count = get_warn_count(chat_id, user_id)

    await update.message.reply_text(
        f"📋 {target.mention_html()}: {count}/3 предупреждений",
        parse_mode="HTML"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    chat_id = str(chat.id)
    member_count = await context.bot.get_chat_member_count(chat.id)
    total_warns = sum(data["warnings"].get(chat_id, {}).values())

    await update.message.reply_text(
        f"📊 *Статистика группы*\n\n"
        f"👥 Участников: {member_count}\n"
        f"⚠️ Активных предупреждений: {total_warns}\n"
        f"💬 Сообщений обработано: {data.get('messages_total', 0)}",
        parse_mode="Markdown"
    )

# ── Auto-moderation ──────────────────────────────────────────────────────────
async def auto_moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    data["messages_total"] = data.get("messages_total", 0) + 1
    save_data(data)

    if is_spam(update.message.text):
        try:
            await update.message.delete()
            await context.bot.send_message(
                update.effective_chat.id,
                f"🚫 Сообщение от {update.effective_user.mention_html()} удалено (спам).",
                parse_mode="HTML"
            )
            # Auto-warn for spam
            chat_id = str(update.effective_chat.id)
            user_id = str(update.effective_user.id)
            count = add_warn(chat_id, user_id)
            if count >= 3:
                await context.bot.ban_chat_member(update.effective_chat.id, update.effective_user.id)
                reset_warns(chat_id, user_id)
                await context.bot.send_message(
                    update.effective_chat.id,
                    f"🔨 {update.effective_user.mention_html()} автоматически забанен за спам.",
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Auto-mod error: {e}")

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    token = "8511371551:AAH3J7LFuZv-C9rrwKOCb0K867zN3xPScE0"

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("warn", warn_user))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("warns", check_warns))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_moderate))

    logger.info("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
