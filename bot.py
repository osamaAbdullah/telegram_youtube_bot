import os
import logging
from pytube import YouTube
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Bot Command Handlers ---
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hi! Send me a YouTube link and I'll download it for you.")

def download_video(update: Update, context: CallbackContext) -> None:
    video_url = update.message.text
    chat_id = update.message.chat_id
    try:
        processing_message = update.message.reply_text("🔗 Processing your link...")
        yt = YouTube(video_url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        if not stream:
            update.message.reply_text("Could not find a downloadable video stream.")
            return

        processing_message.edit_text(f"📥 Downloading '{yt.title}'...")
        video_path = stream.download()

        processing_message.edit_text("📤 Uploading to Telegram...")
        with open(video_path, 'rb') as video_file:
            context.bot.send_video(chat_id=chat_id, video=video_file, caption=yt.title, supports_streaming=True)
        
        processing_message.delete()
        os.remove(video_path)
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("❌ Oops! Something went wrong. Please check the link and try again.")

# --- Main Bot Setup ---
def main() -> None:
    # Get the token from an environment variable for security
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables!")

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))

    # We will use webhooks for deployment, not polling
    #updater.start_polling()
    #updater.idle()
    print("Bot setup complete. Ready for deployment.")


if __name__ == '__main__':
    main()
