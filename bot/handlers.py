# This file will handle user messages and commands

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.database import db_manager
from bot.ai import get_ai_response

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define common greetings that will get static responses
COMMON_GREETINGS = ["hi", "hello", "hey", "hola", "greetings"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    # Store user data when they start the bot
    store_user_data(update)
    await update.message.reply_text(
        "Hi! I'm your Community AI Bot powered by Google Gemini Pro. "
        "Ask me anything, and I'll do my best to help you!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    # Store user data when they use help command
    store_user_data(update)
    await update.message.reply_text(
        "I'm your AI assistant powered by Google Gemini Pro! Here's how to use me:\n\n"
        "• Simple greetings like 'hi' or 'hello' will get a friendly response\n"
        "• For any other questions or topics, I'll use AI to give you the best answer\n"
        "• If you encounter any issues, please contact the admin\n\n"
        "What would you like to know today?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Process user message and respond appropriately:
    - Static responses for common greetings
    - AI-generated responses for all other messages
    """
    # Store user data and message
    store_user_data(update)
    
    # Store the message in database
    user_id = update.effective_user.id
    message_text = update.message.text
    db_manager.add_message(user_id, message_text)
    
    # Log incoming message
    logger.info(f"Received message from user {user_id}: {message_text}")
    
    # Check if the message is a simple greeting
    if message_text.lower() in COMMON_GREETINGS:
        logger.info(f"Responding with static greeting to user {user_id}")
        await update.message.reply_text(f"Hello! How can I help you today?")
    else:
        # Get AI response for all non-greeting messages
        logger.info(f"Requesting AI response for user {user_id}")
        try:
            # Show typing indicator while waiting for AI response
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Get AI response
            ai_response = await get_ai_response(message_text)
            
            # Send the response
            await update.message.reply_text(ai_response)
            logger.info(f"Sent AI response to user {user_id}")
        except Exception as e:
            # Handle any unexpected errors in the message handler
            logger.error(f"Error in message handler: {e}")
            await update.message.reply_text(
                "Sorry, I encountered an unexpected error. Please try again later."
            )

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