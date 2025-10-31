import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters, ContextTypes

# ==== CONFIG ====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8361243003:AAF3PyAyY5cdSUzh2VJyDy-TWjZ2Ionv4x8")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "5400588836"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==== BOT SETUP ====
bot = Bot(TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# ==== HANDLERS ====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "ሰላም፣ ለመመዝገብ 350 ብር በቴሌ ብር ___ ፣ በንግድ ባንክ ቁጥር____ ክፍያዎን ይፈጽሙ። ክፍያውን የፈጸማቹበትን የሚያሳይ ምስል ከላይ ለናሙና በተቀመጠው ምስል መሰረት በዚህ ቦት ይላኩ።"
    )
    if ADMIN_CHAT_ID != 0:
        await update.message.reply_text(f"ADMIN_CHAT_ID is: {ADMIN_CHAT_ID}. Your chat id is: {chat_id}")
        logger.info("Detected chat id: %s", chat_id)

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message.caption:
        await message.reply_text("Enter your name as a caption under the screenshot")
        return

    photo = message.photo[-1]
    file_id = photo.file_id
    caption = message.caption or ""

    try:
        await context.bot.forward_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=message.chat_id,
            message_id=message.message_id
        )
    except Exception as e:
        logger.exception("Forward failed; fallback to send_photo")
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=file_id,
            caption=f"From @{update.effective_user.username or update.effective_user.id}\n{caption}"
        )

    await message.reply_text("Thanks — your screenshot was forwarded to the admin.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please send a screenshot image with your name on the caption to forward to the admin."
    )

# ==== REGISTER HANDLERS ====
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.PHOTO, photo_handler))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

# ==== FLASK APP ====
app = Flask(__name__)

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "Bot is running!"

# ==== MAIN ====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Make sure you set the webhook before starting
    webhook_url = f"https://sewasewbot.onrender.com/{TELEGRAM_TOKEN}"
    bot.delete_webhook()
    bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")
    app.run(host="0.0.0.0", port=port)
