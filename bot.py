import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ChatMemberHandler, ContextTypes, filters
from telegram.constants import ChatMemberStatus
from nudenet import NudeDetector

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "8162343865"))
LOGGER_GROUP_ID = int(os.getenv("LOGGER_GROUP_ID", "-1002724746525"))

detector = NudeDetector()

# ====== Start Message ======
START_MSG = """😎 Welcome to NSFW Protection Bot!  

I’m an AI ☔ powered guardian that keeps your Telegram groups safe & clean.

🛡️ Features:
- Block 🚫 NSFW stickers & images
- Warn ⚠️ + Ban ❌ system
- Active 24/7 🕒  

👨‍💻 Owner: @redhu321  
🔔 Updates: https://t.me/hert_beat_fm_update
"""

# ====== Start Command ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        keyboard = [
            [InlineKeyboardButton("➕ Add Me to Group", url="https://t.me/Scanner_ro_bot?startgroup=s&admin=delete_messages+ban_users")],
            [InlineKeyboardButton("👨‍💻 Owner", url="https://t.me/redhu321")],
            [InlineKeyboardButton("🔔 Updates", url="https://t.me/hert_beat_fm_update")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(START_MSG, reply_markup=reply_markup)

# ====== Sticker/Image Check ======
user_warnings = {}

async def check_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return

    file = None
    if update.message.sticker:
        file = await update.message.sticker.get_file()
    elif update.message.photo:
        file = await update.message.photo[-1].get_file()

    if file:
        file_path = f"/tmp/{file.file_unique_id}.jpg"
        await file.download_to_drive(file_path)

        result = detector.detect(file_path)
        os.remove(file_path)

        if any(r["label"] == "EXPLICIT" and r["score"] > 0.7 for r in result):
            try:
                await update.message.delete()
            except:
                pass

            count = user_warnings.get(user.id, 0) + 1
            user_warnings[user.id] = count

            if count >= 5:
                try:
                    await update.effective_chat.ban_member(user.id)
                    await context.bot.send_message(update.effective_chat.id,
                        f"🚫 {user.mention_html()} banned for NSFW content!", parse_mode="HTML")
                except:
                    pass
            else:
                await update.message.reply_text(
                    f"{user.mention_html()} ⚠️ Warning {count}/5 (NSFW detected)", parse_mode="HTML"
                )

# ====== Bot Status Logger ======
async def track_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    status = update.my_chat_member.new_chat_member.status

    if status == ChatMemberStatus.MEMBER:
        await context.bot.send_message(LOGGER_GROUP_ID,
            f"✅ Added to group: {chat.title}\n🆔 ID: {chat.id}")
    elif status in [ChatMemberStatus.KICKED, ChatMemberStatus.LEFT]:
        await context.bot.send_message(LOGGER_GROUP_ID,
            f"❌ Removed from group: {chat.title}\n🆔 ID: {chat.id}")

# ====== MAIN ======
if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Sticker.ALL | filters.PHOTO, check_media))
    app.add_handler(ChatMemberHandler(track_bot, ChatMemberHandler.MY_CHAT_MEMBER))

    print("🤖 Bot running...")
    app.run_polling()
