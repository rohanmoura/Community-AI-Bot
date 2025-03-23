# This file handles scheduled tasks for the bot

import logging
import datetime
from typing import Dict, Any
from telegram.ext import Application, ContextTypes
from bot.database import db_manager
from bot.utils import send_scheduled_announcement

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def setup_scheduler(application: Application) -> None:
    """Set up scheduled tasks using settings from the database."""
    if application.job_queue is None:
        logger.error("❌ JobQueue is not available. Please install python-telegram-bot[job-queue].")
        return

    settings = db_manager.get_schedule_settings()
    logger.info(f"🟢 Current scheduled jobs: {application.job_queue.jobs()}")

    # Parse daily announcement time and schedule using run_repeating()
    try:
        daily_time = settings.get("daily_time", "09:00")
        # Note: We keep daily_time_obj for logging/comparison purposes
        daily_hour, daily_minute = map(int, daily_time.split(":"))
        daily_time_obj = datetime.time(hour=daily_hour, minute=daily_minute)

        # Schedule daily announcement using run_repeating() to check every 60 seconds.
        application.job_queue.run_repeating(
            daily_announcement,
            interval=60,   # Check every minute
            first=0,
            name="daily_announcement"
        )
        logger.info(f"✅ Daily announcement will trigger when system time equals {daily_time}")
    except Exception as e:
        logger.error(f"⚠️ Failed to schedule daily announcement: {e}")

    # Parse weekly announcement time
    try:
        weekly_time = settings.get("weekly_time", "10:00")
        weekly_day = settings.get("weekly_day", 1)
        weekly_hour, weekly_minute = map(int, weekly_time.split(":"))
        weekly_time_obj = datetime.time(hour=weekly_hour, minute=weekly_minute)

        # Schedule weekly announcement; note: run_daily() with 'days' parameter
        application.job_queue.run_daily(
            weekly_announcement,
            time=weekly_time_obj,
            days=(weekly_day,),
            name="weekly_announcement"
        )
        logger.info(f"✅ Weekly announcement scheduled for day {weekly_day} at {weekly_time}")
    except Exception as e:
        logger.error(f"⚠️ Failed to schedule weekly announcement: {e}")

    logger.info(f"🟢 Final jobs in queue: {application.job_queue.jobs()}")

def reschedule_jobs(application: Application) -> bool:
    """Reschedule jobs with updated settings."""
    try:
        for job in application.job_queue.jobs():
            if job.name in ["daily_announcement", "weekly_announcement"]:
                job.schedule_removal()
                logger.info(f"🗑 Removed job: {job.name}")
        setup_scheduler(application)
        return True
    except Exception as e:
        logger.error(f"⚠️ Failed to reschedule jobs: {e}")
        return False

async def daily_announcement(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check every minute and send a daily announcement to all users when current time matches scheduled time."""
    logger.info("🚀 Daily announcement check triggered!")
    try:
        settings = db_manager.get_schedule_settings()
        scheduled_time = settings.get("daily_time", "09:00")
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        logger.info(f"Daily check: current time {current_time}, scheduled time {scheduled_time}")
        if current_time == scheduled_time:
            messages = db_manager.get_announcement_messages()
            announcement_text = messages.get("daily", "Daily community reminder!")
            context.job.data = {"text": announcement_text}
            logger.info(f"📨 Triggering daily announcement: {announcement_text}")
            await send_scheduled_announcement(context)
            logger.info("✅ Daily announcement sent successfully!")
        else:
            logger.info("Current time does not match scheduled time. No announcement sent.")
    except Exception as e:
        logger.error(f"⚠️ Error in daily announcement: {e}")

async def weekly_announcement(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a weekly announcement to all users."""
    logger.info("🚀 Weekly announcement triggered!")
    try:
        messages = db_manager.get_announcement_messages()
        announcement_text = messages.get("weekly", "Weekly community update!")
        context.job.data = {"text": announcement_text}
        logger.info(f"📨 Sending weekly announcement: {announcement_text}")
        await send_scheduled_announcement(context)
        logger.info("✅ Weekly announcement sent successfully!")
    except Exception as e:
        logger.error(f"⚠️ Error in weekly announcement: {e}")
