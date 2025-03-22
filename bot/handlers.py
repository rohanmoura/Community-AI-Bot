# This file will handle user messages and commands

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.database import db_manager

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    # Store user data when they start the bot
    store_user_data(update)
    await update.message.reply_text("Hi! I'm your test bot. Send 'Hi' to get a response.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    # Store user data when they use help command
    store_user_data(update)
    await update.message.reply_text("Send 'Hi' to get a response!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message and respond to 'Hi'."""
    # Store user data and message
    store_user_data(update)
    
    # Store the message
    user_id = update.effective_user.id
    message_text = update.message.text
    db_manager.add_message(user_id, message_text)
    
    # Check if the message is 'Hi' (case insensitive)
    if message_text.lower() == "hi":
        await update.message.reply_text("Hello")
    else:
        await update.message.reply_text("Send 'Hi' to get a response.")

def store_user_data(update: Update) -> None:
    """Store user data in the database if they don't exist."""
    user = update.effective_user
    
    # Create user data dictionary
    user_data = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name
    }
    
    # Add user to database (this will check if they already exist)
    db_manager.add_user(user_data)