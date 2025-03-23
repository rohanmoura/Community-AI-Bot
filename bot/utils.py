# This file contains utility functions used across the bot

import logging
from typing import Tuple, Dict, Any, List
from telegram.ext import ContextTypes
from bot.database import db_manager

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def send_scheduled_announcement(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a scheduled announcement to all users."""
    if not context.job or not context.job.data:
        logger.error("No job data found for scheduled announcement")
        return
    
    announcement_text = context.job.data.get("text", "")
    if not announcement_text:
        logger.error("No announcement text found in job data")
        return
    
    # Get all users from the database
    users = db_manager.get_all_users()
    success_count = 0
    failure_count = 0
    
    for user in users:
        user_id = user.get("user_id")
        if user_id:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=announcement_text
                )
                success_count += 1
                logger.info(f"Scheduled announcement sent to user {user_id}")
            except Exception as e:
                failure_count += 1
                logger.error(f"Failed to send scheduled announcement to user {user_id}: {e}")
    
    logger.info(f"Scheduled announcement complete: {success_count} successful, {failure_count} failed")

async def broadcast_message(context: ContextTypes.DEFAULT_TYPE, message: str) -> Tuple[int, int]:
    """
    Broadcast a message to all users in the database.
    Returns a tuple of (success_count, failure_count)
    """
    logger.info(f"🔊 Broadcasting message to all users: {message[:50]}...")
    users = db_manager.get_all_users()
    success_count = 0
    failure_count = 0
    
    for user in users:
        user_id = user.get("user_id")
        if user_id:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message
                )
                success_count += 1
                logger.info(f"✅ Broadcast message sent to user {user_id}")
            except Exception as e:
                failure_count += 1
                logger.error(f"⚠️ Failed to send broadcast message to user {user_id}: {e}")
    
    logger.info(f"Broadcast complete: {success_count} successful, {failure_count} failed")
    return success_count, failure_count
