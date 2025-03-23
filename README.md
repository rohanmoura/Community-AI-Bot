# Community-AI-Bot

AI Telegram bot for community management with automated responses and engagement features.

## Features

- **AI-Powered Responses**: Uses Google Gemini Pro to provide intelligent responses to user queries
- **Admin Management**: Add, remove, and list admins with proper access control
- **Scheduled Announcements**: Set up daily and weekly announcements to engage your community
- **Broadcast Messages**: Send announcements to all users in your community
- **Admin Notifications**: Automatic notifications when admin status changes

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- MongoDB database
- Telegram Bot Token (from BotFather)
- Google Gemini API key (for AI responses)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Community-AI-Bot.git
   cd Community-AI-Bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   `
   ``
3. Create a .env file in the root directory with the following variables:

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
MONGODB_URI=your_mongodb_connection_string
GEMINI_API_KEY=your_gemini_api_key
DEFAULT_ADMIN_ID=your_telegram_user_id

4. Run the bot:
   ```bash
   python main.py
   ```

## Admin Commands
The bot supports the following admin commands:

- /start - Start the bot and get a welcome message
- /help - Display help information about available commands
- /announce - Send an announcement to all users
- /addadmin - Add a new admin by Telegram user ID
- /removeadmin - Remove an admin by Telegram user ID
- /listadmins - List all current admins
- /setschedule - Configure scheduled announcements (daily or weekly)

## Scheduled Announcements
The bot can send automated announcements to all users:

### Daily Announcements
- Set a specific time for daily announcements
- Customize the message content
### Weekly Announcements
- Set a specific day and time for weekly announcements
- Customize the message content
## Admin Management
### Adding an Admin
1. Use the /addadmin command
2. Enter the Telegram user ID of the new admin
3. All users will be notified of the new admin addition
### Removing an Admin
1. Use the /removeadmin command
2. Enter the Telegram user ID of the admin to remove
3. All users will be notified of the admin removal
4. The removed admin will receive a direct notification
## Development
### Project Structure
- main.py - Entry point for the application
- bot/ - Main module directory
  - ai.py - AI response handling
  - commands.py - Admin command handlers
  - database.py - Database operations
  - handlers.py - Message handlers
  - scheduler.py - Scheduled tasks
  - utils.py - Utility functions
  - config.py - Configuration settings
### Adding New Features
To add new features, follow these steps:

1. Create appropriate handlers in the relevant module
2. Register the handlers in main.py
3. Update documentation in this README