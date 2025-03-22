# Main file to run the Telegram bot

import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Load environment variables
load_dotenv()

# Import handlers from handlers.py
from bot.handlers import start, help_command, handle_message

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    # Get the token from environment variables
    token = os.getenv("TELEGRAM_API_KEY")
    if not token:
        logger.error("No TELEGRAM_API_KEY found in environment variables!")
        return
    
    # Create the Application and pass it your bot's token
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()