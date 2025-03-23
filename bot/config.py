# This File will store the bot token and any important settings.

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get default admin ID for initial setup
DEFAULT_ADMIN_ID = os.getenv("DEFAULT_ADMIN_ID", "")

# Scheduled announcement default settings
# These are only used as fallbacks if database settings are unavailable
DEFAULT_DAILY_TIME = "09:00"  # Format: HH:MM
DEFAULT_WEEKLY_DAY = 1  # 0=Monday, 6=Sunday
DEFAULT_WEEKLY_TIME = "10:00"  # Format: HH:MM

# Check if default admin ID is configured
if not DEFAULT_ADMIN_ID:
    print("Warning: No default admin ID configured. Set DEFAULT_ADMIN_ID in your .env file.")

# Get admin IDs from environment variables
# Format in .env file: ADMIN_IDS=123456789,987654321
admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id_str) for id_str in admin_ids_str.split(",") if id_str.strip().isdigit()]

# Scheduled announcement settings
DAILY_ANNOUNCEMENT_TIME = os.getenv("DAILY_ANNOUNCEMENT_TIME", "09:00")  # Format: HH:MM
WEEKLY_ANNOUNCEMENT_DAY = int(os.getenv("WEEKLY_ANNOUNCEMENT_DAY", "1"))  # 0=Monday, 6=Sunday
WEEKLY_ANNOUNCEMENT_TIME = os.getenv("WEEKLY_ANNOUNCEMENT_TIME", "10:00")  # Format: HH:MM

# Check if admin IDs are configured
if not ADMIN_IDS:
    print("Warning: No admin IDs configured. Set ADMIN_IDS in your .env file.")