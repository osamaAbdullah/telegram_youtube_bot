import os
import logging
from pytube import YouTube
from telegram import Update
# Note the new imports: Application, ContextTypes, and filters
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Bot Command Handlers ---
# All handler functions are now 'async def'
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user = update.effective_user
    welcome_message = (
        f"Hi {user.first_name}!\n\n"
        "Just send me a YouTube video link and I'll download and send it to you."
    )
    # API calls like reply_text must now be 'await'ed
    await update.message.reply_text(welcome_message)

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles messages containing YouTube links."""
    video_url = update.message.text
    chat_id = update.message.chat_id

    try:
        # Initial feedback to the user
        processing_message = await update.message.reply_text("🔗 Got your link! Processing...")
        
        yt = YouTube(video_url)
        
        # Filter for progressive mp4 streams and get the highest resolution
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        if not stream:
            await update.message.reply_text("Couldn't find a downloadable video stream.")
            return

        await processing_message.edit_text(f"✅ Found it! Downloading '{yt.title}'...")

        # Download the video
        video_path = stream.download()

        await processing_message.edit_text("📥 Download complete! Uploading to Telegram...")

        # Send the video file to the user
        with open(video_path, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption=yt.title,
                supports_streaming=True
            )
        
        # Clean up
        await processing_message.delete()
        os.remove(video_path)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        await update.message.reply_text(
            "❌ Oops! Something went wrong. Please make sure you sent a valid YouTube video URL."
        )

# --- Main Bot Setup ---
def main() -> None:
    """Start the bot."""
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables!")

    # The main function now uses the new Application builder pattern
    application = Application.builder().token(TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))

    # The MessageHandler now uses filters.TEXT & ~filters.COMMAND
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    # Start the Bot by polling
    print("Bot is starting...")
    application.run_polling()


if __name__ == '__main__':
    main()
