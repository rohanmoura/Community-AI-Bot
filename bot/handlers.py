# This file contains message handlers for the bot

import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes
from bot.database import db_manager
from bot.ai import generate_ai_response

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def store_user_data(update: Update) -> None:
    """Store user data in the database."""
    user = update.effective_user
    user_data = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name
    }
    db_manager.add_user(user_data)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    # Store user data when they start the bot
    store_user_data(update)
    
    # Check if there are any admins in the database
    admins = db_manager.get_all_admins()
    user_id = update.effective_user.id
    
    # If no admins exist, make this user an admin
    if not admins:
        if db_manager.add_admin(user_id, "system"):
            await update.message.reply_text(
                f"Welcome! You are the first user, so I've made you an admin.\n\n"
                f"Your user ID is: {user_id}\n\n"
                f"Type /help to see available commands."
            )
            return
    
    # Regular welcome message
    await update.message.reply_text(
        f"Welcome to the Community AI Bot! I'm here to help answer your questions.\n\n"
        f"Type /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    # Store user data when they use help command
    store_user_data(update)
    
    # Check if the user is an admin
    user_id = update.effective_user.id
    is_admin = db_manager.is_admin(user_id)
    
    # Base help message for all users
    help_message = (
        "I'm your AI assistant powered by Google Gemini Pro! Here's how to use me:\n\n"
        "Just send me a message, and I'll respond with an AI-generated answer.\n\n"
        "Available commands for all users:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/motivate - Get an AI-generated motivational message\n"
    )
    
    # Additional commands for admins
    if is_admin:
        help_message += (
            "\nAdmin commands:\n"
            "/announce - Send an announcement to all users\n"
            "/addadmin - Add a new admin\n"
            "/removeadmin - Remove an admin\n"
            "/listadmins - List all admins\n"
            "/setschedule - Configure scheduled announcements\n"
        )
    
    await update.message.reply_text(help_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the user message and respond with AI."""
    # Store user data and message
    store_user_data(update)
    user_id = update.effective_user.id
    message_text = update.message.text
    db_manager.add_message(user_id, message_text)
    
    # Generate AI response
    try:
        # Send typing action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Get AI response
        response = await generate_ai_response(message_text)
        
        # Send the response
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        await update.message.reply_text(
            "I'm sorry, I couldn't generate a response at the moment. Please try again later."
        )