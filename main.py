import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Load environment variables first to ensure they're available
load_dotenv()

# Import handlers from bot modules
from bot.handlers import start, help_command, handle_message
from bot.commands import (
    announcement_handler, 
    add_admin_handler, 
    remove_admin_handler, 
    schedule_handler,
    list_admins_handler,
    motivate_handler  # Add the new motivate handler import
)
from bot.scheduler import setup_scheduler
from bot.database import db_manager

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot and set up all handlers and scheduled tasks."""
    # Get the bot token from environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No bot token provided. Set TELEGRAM_BOT_TOKEN in your .env file.")
        return

    # Check database connection
    logger.info("🔄 Checking database connection...")
    if not db_manager.check_connection():
        logger.error("❌ Database connection failed. Please check your MongoDB URI and credentials.")
        logger.info("⚠️ Bot will start, but data persistence may not work correctly.")
    else:
        logger.info("✅ Database connection successful!")

    # Create the Application instance
    application = Application.builder().token(token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add conversation handlers for admin commands
    application.add_handler(announcement_handler)
    application.add_handler(add_admin_handler)
    application.add_handler(remove_admin_handler)
    application.add_handler(schedule_handler)
    application.add_handler(list_admins_handler)
    application.add_handler(motivate_handler)  # Add the new motivate handler
    
    # Add message handler for regular messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Set up scheduled tasks
    setup_scheduler(application)
    
    # Start the Bot
    logger.info("🚀 Starting bot...")
    application.run_polling()
    
    logger.info("✅ Bot started successfully!")

if __name__ == "__main__":
    main()
