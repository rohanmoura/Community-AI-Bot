# This file will handle user messages and commands

import logging
from telegram import Update
from telegram.ext import ContextTypes

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