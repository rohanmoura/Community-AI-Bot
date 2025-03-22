# This file will used for testing bot functionalities.
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text("Hi! I'm your test bot. Send 'Hi' to get a response.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Send 'Hi' to get a response!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message and respond to 'Hi'."""
    text = update.message.text
    
    # Check if the message is 'Hi' (case insensitive)
    if text.lower() == "hi":
        await update.message.reply_text("Hello")
    else:
        await update.message.reply_text("Send 'Hi' to get a response.")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token("7438550679:AAFdClqhji4ZghjpA7aOtj9rMtF2oqd7Y20").build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()