# This file will handle admin commands (e.g., announcements, scheduled updates)

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    ConversationHandler, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    CallbackQueryHandler
)
from bot.database import db_manager
from bot.utils import send_scheduled_announcement, broadcast_message
from bot.scheduler import reschedule_jobs

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

#------------------------------------------------------------------------------
# Conversation states
#------------------------------------------------------------------------------

# Announcement states
TYPING_ANNOUNCEMENT = 0
CONFIRM_ANNOUNCEMENT = 1

# Admin management states
TYPING_ADMIN_ID = 0

# Schedule management states
CHOOSING_SCHEDULE_TYPE = 0
TYPING_ANNOUNCEMENT_MESSAGE = 1
TYPING_TIME = 2
TYPING_DAY = 3
CONFIRM_SCHEDULE = 4

# Callback data constants
DAILY_SCHEDULE = "daily_schedule"
WEEKLY_SCHEDULE = "weekly_schedule"
CONFIRM_SCHEDULE_UPDATE = "confirm_schedule"
CANCEL_SCHEDULE_UPDATE = "cancel_schedule"

#------------------------------------------------------------------------------
# Helper functions
#------------------------------------------------------------------------------

def format_time_ampm(time_24h: str) -> str:
    """Convert 24-hour format to 12-hour AM/PM format."""
    try:
        hour, minute = map(int, time_24h.split(':'))
        period = "AM" if hour < 12 else "PM"
        hour = hour % 12
        if hour == 0:
            hour = 12
        return f"{hour}:{minute:02d} {period}"
    except Exception as e:
        logger.error(f"Error formatting time: {e}")
        return time_24h

def parse_time_ampm(time_ampm: str) -> str:
    """Convert 12-hour AM/PM format to 24-hour format."""
    try:
        # Regular expression to match time in format like "9:30 AM" or "12:45 PM"
        match = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_ampm.upper())
        if not match:
            return None
            
        hour, minute, period = match.groups()
        hour = int(hour)
        minute = int(minute)
        
        # Convert to 24-hour format
        if period == "PM" and hour < 12:
            hour += 12
        elif period == "AM" and hour == 12:
            hour = 0
            
        return f"{hour:02d}:{minute:02d}"
    except Exception as e:
        logger.error(f"Error parsing time: {e}")
        return None

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    await update.message.reply_text(
        "Operation cancelled. What would you like to do next?"
    )
    return ConversationHandler.END

async def is_admin(update: Update) -> bool:
    """
    Check if the user is an admin by querying the database.
    This function always performs a fresh database check to ensure accuracy.
    """
    user_id = update.effective_user.id
    # Always perform a fresh database check
    is_admin_status = db_manager.is_admin(user_id)
    logger.info(f"Admin status check for user {user_id}: {is_admin_status}")
    return is_admin_status

#------------------------------------------------------------------------------
# Announcement command handlers
#------------------------------------------------------------------------------

async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process to send an announcement to all users."""
    # Check if user is admin
    if not await is_admin(update):
        await update.message.reply_text(
            "⛔ Access Denied: This command is only available to admins. "
            "You are not registered as an admin in the system."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "Please enter the announcement message you want to send to all users:"
    )
    return TYPING_ANNOUNCEMENT

async def announcement_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the announcement message and ask for confirmation."""
    # Store the announcement text
    context.user_data["announcement_text"] = update.message.text
    
    # Create confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton("Send", callback_data="send_announcement"),
            InlineKeyboardButton("Cancel", callback_data="cancel_announcement"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📢 Announcement Preview:\n\n{update.message.text}\n\nDo you want to send this to all users?",
        reply_markup=reply_markup
    )
    return CONFIRM_ANNOUNCEMENT

async def announcement_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the confirmation of the announcement."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_announcement":
        await query.edit_message_text("Announcement cancelled.")
        return ConversationHandler.END
    
    # Get the announcement text
    announcement_text = context.user_data.get("announcement_text", "")
    if not announcement_text:
        await query.edit_message_text("Error: No announcement text found.")
        return ConversationHandler.END
    
    # Send the announcement to all users
    users = db_manager.get_all_users()
    success_count = 0
    failure_count = 0
    
    for user in users:
        user_id = user.get("user_id")
        if user_id:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 ANNOUNCEMENT 📢\n\n{announcement_text}"
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send announcement to user {user_id}: {e}")
                failure_count += 1
    
    # Update the confirmation message
    await query.edit_message_text(
        f"Announcement sent to {success_count} users. ({failure_count} failed)"
    )
    return ConversationHandler.END

#------------------------------------------------------------------------------
# Admin management command handlers
#------------------------------------------------------------------------------

async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process to add a new admin."""
    # Check if user is admin
    if not await is_admin(update):
        await update.message.reply_text(
            "⛔ Access Denied: This command is only available to admins. "
            "You are not registered as an admin in the system."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "Please enter the Telegram user ID of the new admin:"
    )
    return TYPING_ADMIN_ID

async def admin_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the admin ID input."""
    admin_id_text = update.message.text.strip()
    
    # Validate the admin ID
    if not admin_id_text.isdigit():
        await update.message.reply_text(
            "Invalid user ID. Please enter a numeric ID."
        )
        return TYPING_ADMIN_ID
    
    admin_id = int(admin_id_text)
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Add the new admin
    if db_manager.add_admin(admin_id, user_id, username):
        await update.message.reply_text(
            f"User with ID {admin_id} has been added as an admin."
        )
        
        # Broadcast notification to all users
        admin_user = db_manager.get_user(admin_id)
        admin_username = admin_user.get("username", "Unknown") if admin_user else "Unknown"
        notification_message = f"🔔 ADMIN UPDATE 🔔\n\nUser @{admin_username} (ID: {admin_id}) has been added as an admin."
        success_count, failure_count = await broadcast_message(context, notification_message)
        
        await update.message.reply_text(
            f"Notification sent to {success_count} users. ({failure_count} failed)"
        )
    else:
        await update.message.reply_text(
            f"Failed to add user with ID {admin_id} as an admin. Please try again later."
        )
    
    return ConversationHandler.END

async def remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process to remove an admin."""
    # Check if user is admin
    if not await is_admin(update):
        await update.message.reply_text(
            "⛔ Access Denied: This command is only available to admins. "
            "You are not registered as an admin in the system."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "Please enter the Telegram user ID of the admin to remove:"
    )
    return TYPING_ADMIN_ID

async def remove_admin_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the admin ID input for removal."""
    admin_id_text = update.message.text.strip()
    
    # Validate the admin ID
    if not admin_id_text.isdigit():
        await update.message.reply_text(
            "Invalid user ID. Please enter a numeric ID."
        )
        return TYPING_ADMIN_ID
    
    admin_id = int(admin_id_text)
    
    # Prevent removing yourself
    if admin_id == update.effective_user.id:
        await update.message.reply_text(
            "You cannot remove yourself as an admin."
        )
        return ConversationHandler.END
    
    # Get admin info before removal for notification
    admin_user = db_manager.get_user(admin_id)
    admin_username = admin_user.get("username", "Unknown") if admin_user else "Unknown"
    
    # Remove the admin
    if db_manager.remove_admin(admin_id):
        await update.message.reply_text(
            f"User with ID {admin_id} has been removed from admins."
        )
        
        # Broadcast notification to all users
        notification_message = f"🔔 ADMIN UPDATE 🔔\n\nUser @{admin_username} (ID: {admin_id}) has been removed from admin role."
        success_count, failure_count = await broadcast_message(context, notification_message)
        
        # Send a direct message to the removed admin
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text="🔔 ADMIN STATUS UPDATE 🔔\n\nYour admin privileges have been revoked. "
                     "You no longer have access to admin commands."
            )
            logger.info(f"Sent admin removal notification to user {admin_id}")
        except Exception as e:
            logger.error(f"Failed to send admin removal notification to user {admin_id}: {e}")
        
        await update.message.reply_text(
            f"Notification sent to {success_count} users. ({failure_count} failed)"
        )
    else:
        await update.message.reply_text(
            f"Failed to remove user with ID {admin_id} from admins. Please check if the ID is correct."
        )
    
    return ConversationHandler.END

# Create conversation handler for removing admins
remove_admin_handler = ConversationHandler(
    entry_points=[CommandHandler("removeadmin", remove_admin_command)],
    states={
        TYPING_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_admin_id_input)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# Function to list all admins
# Make sure this exists in your commands.py file
async def list_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all admins."""
    # Check if user is admin
    if not await is_admin(update):
        await update.message.reply_text(
            "⛔ Access Denied: This command is only available to admins. "
            "You are not registered as an admin in the system."
        )
        return
    
    # Get all admins
    admins = db_manager.get_all_admins()
    
    if not admins:
        await update.message.reply_text("No admins found in the database.")
        return
    
    # Format the admin list
    admin_list = "📋 Admin List:\n\n"
    for i, admin in enumerate(admins, 1):
        admin_id = admin.get("user_id", "Unknown")
        added_at = admin.get("added_at", "Unknown")
        added_by = admin.get("added_by", "Unknown")
        
        admin_list += f"{i}. Admin ID: {admin_id}\n"
        admin_list += f"   Added at: {added_at}\n"
        admin_list += f"   Added by: {added_by}\n\n"
    
    await update.message.reply_text(admin_list)

# Define the handler
list_admins_handler = CommandHandler("listadmins", list_admins_command)

#------------------------------------------------------------------------------
# Schedule management command handlers
#------------------------------------------------------------------------------

async def set_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process to set up scheduled announcements."""
    # Check if user is admin
    if not await is_admin(update):
        await update.message.reply_text(
            "⛔ Access Denied: This command is only available to admins. "
            "You are not registered as an admin in the system."
        )
        return ConversationHandler.END
    
    # Create keyboard for schedule type selection
    keyboard = [
        [
            InlineKeyboardButton("Daily Announcement", callback_data=DAILY_SCHEDULE),
            InlineKeyboardButton("Weekly Announcement", callback_data=WEEKLY_SCHEDULE),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Please select the type of scheduled announcement you want to set up:",
        reply_markup=reply_markup
    )
    return CHOOSING_SCHEDULE_TYPE

async def schedule_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the schedule type selection."""
    query = update.callback_query
    await query.answer()
    
    # Store the schedule type in user_data
    context.user_data["schedule_type"] = query.data
    
    if query.data == DAILY_SCHEDULE:
        await query.edit_message_text(
            "You've selected Daily Announcement.\n\n"
            "Please enter the message for the daily announcement:"
        )
    else:  # WEEKLY_SCHEDULE
        await query.edit_message_text(
            "You've selected Weekly Announcement.\n\n"
            "Please enter the message for the weekly announcement:"
        )
    
    return TYPING_ANNOUNCEMENT_MESSAGE

async def announcement_message_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the announcement message input."""
    # Store the announcement message
    context.user_data["announcement_message"] = update.message.text
    
    # Ask for the time based on schedule type
    if context.user_data.get("schedule_type") == DAILY_SCHEDULE:
        await update.message.reply_text(
            "Please enter the time for the daily announcement (e.g., 9:00 AM or 14:30):"
        )
    else:  # WEEKLY_SCHEDULE
        await update.message.reply_text(
            "Please enter the time for the weekly announcement (e.g., 9:00 AM or 14:30):"
        )
    
    return TYPING_TIME

async def time_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the time input."""
    time_input = update.message.text.strip()
    
    # Try to parse the time
    time_24h = parse_time_ampm(time_input)
    if not time_24h:
        # Try to parse as 24-hour format directly
        try:
            # Check if it matches HH:MM format
            if re.match(r"^\d{1,2}:\d{2}$", time_input):
                hour, minute = map(int, time_input.split(':'))
                if 0 <= hour < 24 and 0 <= minute < 60:
                    time_24h = f"{hour:02d}:{minute:02d}"
        except Exception:
            time_24h = None
    
    if not time_24h:
        await update.message.reply_text(
            "Invalid time format. Please enter a time in format like '9:00 AM' or '14:30':"
        )
        return TYPING_TIME
    
    # Store the time
    context.user_data["time"] = time_24h
    
    # If it's a weekly schedule, ask for the day
    if context.user_data.get("schedule_type") == WEEKLY_SCHEDULE:
        keyboard = [
            [
                InlineKeyboardButton("Monday", callback_data="1"),
                InlineKeyboardButton("Tuesday", callback_data="2"),
                InlineKeyboardButton("Wednesday", callback_data="3"),
            ],
            [
                InlineKeyboardButton("Thursday", callback_data="4"),
                InlineKeyboardButton("Friday", callback_data="5"),
                InlineKeyboardButton("Saturday", callback_data="6"),
            ],
            [
                InlineKeyboardButton("Sunday", callback_data="0"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Please select the day for the weekly announcement:",
            reply_markup=reply_markup
        )
        return TYPING_DAY
    else:
        # For daily schedule, go directly to confirmation
        return await show_schedule_confirmation(update, context)

async def day_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the day input."""
    query = update.callback_query
    await query.answer()
    
    # Store the day
    context.user_data["day"] = int(query.data)
    
    # Show confirmation
    await query.edit_message_text("Day selected. Preparing confirmation...")
    return await show_schedule_confirmation(update, context)

async def show_schedule_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the schedule confirmation."""
    schedule_type = context.user_data.get("schedule_type")
    announcement_message = context.user_data.get("announcement_message", "")
    time_24h = context.user_data.get("time", "")
    day = context.user_data.get("day")
    
    # Format the time for display
    time_display = format_time_ampm(time_24h)
    
    # Create the confirmation message
    if schedule_type == DAILY_SCHEDULE:
        confirmation_message = (
            f"📅 Daily Announcement Settings:\n\n"
            f"⏰ Time: {time_display}\n"
            f"📝 Message:\n{announcement_message}\n\n"
            f"Do you want to save these settings?"
        )
    else:  # WEEKLY_SCHEDULE
        day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        day_name = day_names[day]
        
        confirmation_message = (
            f"📅 Weekly Announcement Settings:\n\n"
            f"📆 Day: {day_name}\n"
            f"⏰ Time: {time_display}\n"
            f"📝 Message:\n{announcement_message}\n\n"
            f"Do you want to save these settings?"
        )
    
    # Create confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data=CONFIRM_SCHEDULE_UPDATE),
            InlineKeyboardButton("Cancel", callback_data=CANCEL_SCHEDULE_UPDATE),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit the message based on update type
    if update.callback_query:
        await update.callback_query.edit_message_text(
            confirmation_message,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            confirmation_message,
            reply_markup=reply_markup
        )
    
    return CONFIRM_SCHEDULE

async def schedule_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the schedule confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == CANCEL_SCHEDULE_UPDATE:
        await query.edit_message_text("Schedule update cancelled.")
        return ConversationHandler.END
    
    # Get the data from user_data
    schedule_type = context.user_data.get("schedule_type")
    announcement_message = context.user_data.get("announcement_message", "")
    time_24h = context.user_data.get("time", "")
    day = context.user_data.get("day")
    
    # Update the database based on schedule type
    success = False
    if schedule_type == DAILY_SCHEDULE:
        success = db_manager.update_schedule_settings(
            daily_time=time_24h,
            daily_message=announcement_message
        )
    else:  # WEEKLY_SCHEDULE
        success = db_manager.update_schedule_settings(
            weekly_time=time_24h,
            weekly_day=day,
            weekly_message=announcement_message
        )
    
    if success:
        # Reschedule the jobs
        if reschedule_jobs(context.application):
            await query.edit_message_text("✅ Schedule settings updated successfully!")
        else:
            await query.edit_message_text(
                "⚠️ Settings saved but failed to reschedule jobs. "
                "Please restart the bot to apply changes."
            )
    else:
        await query.edit_message_text("❌ Failed to update schedule settings. Please try again later.")
    
    return ConversationHandler.END

# Create conversation handler for schedule management
schedule_handler = ConversationHandler(
    entry_points=[CommandHandler("setschedule", set_schedule_command)],
    states={
        CHOOSING_SCHEDULE_TYPE: [
            CallbackQueryHandler(schedule_type_selection, pattern=f"^{DAILY_SCHEDULE}$|^{WEEKLY_SCHEDULE}$")
        ],
        TYPING_ANNOUNCEMENT_MESSAGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, announcement_message_input)
        ],
        TYPING_TIME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, time_input)
        ],
        TYPING_DAY: [
            CallbackQueryHandler(day_input, pattern="^[0-6]$")
        ],
        CONFIRM_SCHEDULE: [
            CallbackQueryHandler(
                schedule_confirmation, 
                pattern=f"^{CONFIRM_SCHEDULE_UPDATE}$|^{CANCEL_SCHEDULE_UPDATE}$"
            )
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# After the list_admins_command function, add this line:
# Create conversation handler for adding admins
add_admin_handler = ConversationHandler(
    entry_points=[CommandHandler("addadmin", add_admin_command)],
    states={
        TYPING_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_id_input)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# Create conversation handler for announcements
announcement_handler = ConversationHandler(
    entry_points=[CommandHandler("announce", announce_command)],
    states={
        TYPING_ANNOUNCEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, announcement_input)],
        CONFIRM_ANNOUNCEMENT: [CallbackQueryHandler(announcement_confirmation, pattern="^send_announcement$|^cancel_announcement$")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

#------------------------------------------------------------------------------
# Motivational message command handler
#------------------------------------------------------------------------------

async def motivate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send a motivational message to the user."""
    try:
        # Send typing action to show the bot is processing
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Import the AI generation function
        from bot.ai import generate_ai_response
        
        # Create a prompt for a motivational message
        prompt = "Generate a short, uplifting motivational message to inspire community members. Keep it concise, positive, and energizing."
        
        # Generate the motivational message using the AI
        motivational_message = await generate_ai_response(prompt)
        
        # Format the message with emojis for better presentation
        formatted_message = f"✨ *Daily Motivation* ✨\n\n{motivational_message}"
        
        # Send the motivational message to the user
        await update.message.reply_text(
            formatted_message,
            parse_mode="Markdown"
        )
        
        # Log the successful generation
        logger.info(f"Motivational message generated for user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error generating motivational message: {e}")
        await update.message.reply_text(
            "I'm sorry, I couldn't generate a motivational message right now. Please try again later."
        )

# Create a command handler for the motivate command
motivate_handler = CommandHandler("motivate", motivate_command)