# This file handles all database operations for the bot

import logging
import datetime
import pymongo
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _client = None
    _db = None
    _users_collection = None
    _admins_collection = None
    _settings_collection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._connect_to_db()
        return cls._instance

    @classmethod
    def _connect_to_db(cls) -> None:
        """Connect to MongoDB database."""
        try:
            import os
            from dotenv import load_dotenv
            
            # Load environment variables
            load_dotenv()
            
            # Get MongoDB URI from environment variables
            mongodb_uri = os.getenv("MONGODB_URI")
            # Use a consistent database name - changed from "community_ai_bot" to match your setup
            db_name = os.getenv("DB_NAME", "telegram_bot")
            
            if not mongodb_uri:
                logger.error("❌ MONGODB_URI environment variable is not set!")
                return
                
            logger.info(f"🔄 Attempting to connect to MongoDB with URI: {mongodb_uri[:20]}...")
            
            # Connect to MongoDB with a timeout to avoid hanging
            cls._client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            
            # Test the connection by making a simple call
            cls._client.admin.command('ping')
            
            cls._db = cls._client[db_name]
            logger.info(f"✅ Connected to MongoDB database: {db_name}")
            
            # Initialize collections
            cls._users_collection = cls._db["users"]
            cls._admins_collection = cls._db["admins"]
            cls._settings_collection = cls._db["settings"]
            
            # Create indexes
            cls._users_collection.create_index("user_id", unique=True)
            cls._admins_collection.create_index("user_id", unique=True)
            
            # Initialize settings if they don't exist
            cls._initialize_defaults()
            
        except pymongo.errors.ServerSelectionTimeoutError as e:
            logger.error(f"❌ MongoDB connection timeout: {e}")
            cls._reset_connection()
        except pymongo.errors.ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failure: {e}")
            cls._reset_connection()
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            cls._reset_connection()

    @classmethod
    def _reset_connection(cls):
        """Reset all connection-related attributes."""
        cls._client = None
        cls._db = None
        cls._users_collection = None
        cls._admins_collection = None
        cls._settings_collection = None

    @classmethod
    def _initialize_defaults(cls) -> None:
        """Initialize default settings in the database."""
        try:
            if cls._settings_collection is None:
                logger.error("❌ Cannot initialize defaults: settings collection is None")
                return
                
            # Check if settings document exists
            settings_count = cls._settings_collection.count_documents({})
            logger.info(f"📊 Found {settings_count} settings documents")
            
            if settings_count == 0:
                default_settings = {
                    "daily_time": "09:00",
                    "weekly_time": "10:00",
                    "weekly_day": 1,  # Monday
                    "messages": {
                        "daily": "Daily community reminder!",
                        "weekly": "Weekly community update!"
                    }
                }
                
                result = cls._settings_collection.insert_one(default_settings)
                if result.inserted_id:
                    logger.info(f"✅ Initialized default settings: {default_settings}")
                else:
                    logger.error("❌ Failed to insert default settings")
        except Exception as e:
            logger.error(f"❌ Error initializing defaults: {e}")

    #--------------------------------------------------------------------------
    # User management methods
    #--------------------------------------------------------------------------
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a user by their ID."""
        if self._users_collection is None:
            logger.error("Database connection not established")
            return None
        try:
            return self._users_collection.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users from the database."""
        if self._users_collection is None:
            logger.error("Database connection not established")
            return []
        try:
            return list(self._users_collection.find())
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

    def add_user(self, user_data: Dict[str, Any]) -> bool:
        """Add a new user or update an existing user."""
        if self._users_collection is None:
            logger.error("❌ Database connection not established - cannot add user")
            return False
        
        if "user_id" not in user_data:
            logger.error("❌ Cannot add user: missing user_id in user_data")
            return False
            
        try:
            user_id = user_data["user_id"]
            logger.info(f"🔄 Adding/updating user with ID: {user_id}")
            
            existing_user = self.get_user(user_id)
            if existing_user:
                # Update existing user
                update_data = {
                    "username": user_data.get("username"),
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "last_active": datetime.datetime.utcnow().isoformat() + "Z"
                }
                
                result = self._users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    logger.info(f"✅ Updated user {user_id}")
                else:
                    logger.warning(f"⚠️ User {user_id} update had no effect")
                return True
            else:
                # Add new user
                user_data["created_at"] = datetime.datetime.utcnow().isoformat() + "Z"
                user_data["last_active"] = user_data["created_at"]
                user_data["messages"] = []
                
                result = self._users_collection.insert_one(user_data)
                if result.inserted_id:
                    logger.info(f"✅ Added new user {user_id}")
                    return True
                else:
                    logger.error(f"❌ Failed to insert new user {user_id}")
                    return False
        except pymongo.errors.DuplicateKeyError:
            logger.warning(f"⚠️ Duplicate key error for user {user_data.get('user_id')}")
            return False
        except Exception as e:
            logger.error(f"❌ Error adding/updating user: {e}")
            return False

    def add_message(self, user_id: int, message_text: str) -> bool:
        """Add a message to a user's history."""
        if self._users_collection is None:
            logger.error("Database connection not established")
            return False
        try:
            message = {"text": message_text, "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}
            result = self._users_collection.update_one({"user_id": user_id}, {"$push": {"messages": message}})
            if result.modified_count > 0:
                logger.info(f"Added message for user {user_id}")
                return True
            else:
                logger.warning(f"User {user_id} not found when adding message")
                return False
        except Exception as e:
            logger.error(f"Error adding message for user {user_id}: {e}")
            return False

    #--------------------------------------------------------------------------
    # Admin management methods
    #--------------------------------------------------------------------------
    
    def is_admin(self, user_id: int) -> bool:
        """Check if a user is an admin."""
        if self._admins_collection is None:
            logger.error("Database connection not established")
            return False
        try:
            admin = self._admins_collection.find_one({"user_id": user_id})
            return admin is not None
        except Exception as e:
            logger.error(f"Error checking admin status for user {user_id}: {e}")
            return False

    def add_admin(self, user_id: int, added_by: int, added_by_username: str = None) -> bool:
        """Add a new admin."""
        if self._admins_collection is None:
            logger.error("❌ Database connection not established - cannot add admin")
            return False
        try:
            logger.info(f"🔄 Adding admin with ID: {user_id}, added by: {added_by}")
            
            # Check if user is already an admin
            if self.is_admin(user_id):
                logger.info(f"ℹ️ User {user_id} is already an admin")
                return True
                
            admin_data = {
                "user_id": user_id,
                "added_at": datetime.datetime.utcnow().isoformat() + "Z",
                "added_by": added_by
            }
            if added_by_username:
                admin_data["added_by_username"] = added_by_username
                
            result = self._admins_collection.insert_one(admin_data)
            if result.inserted_id:
                logger.info(f"✅ Added new admin with ID {user_id}")
                return True
            else:
                logger.error(f"❌ Failed to insert new admin {user_id}")
                return False
        except pymongo.errors.DuplicateKeyError:
            logger.warning(f"⚠️ Duplicate key error for admin {user_id}")
            # User is already an admin, so return True
            return True
        except Exception as e:
            logger.error(f"❌ Error adding admin: {e}")
            return False

    def remove_admin(self, user_id: int) -> bool:
        """Remove an admin."""
        if self._admins_collection is None:
            logger.error("Database connection not established")
            return False
        try:
            result = self._admins_collection.delete_one({"user_id": user_id})
            if result.deleted_count > 0:
                logger.info(f"Removed admin with ID {user_id}")
                return True
            else:
                logger.warning(f"Admin with ID {user_id} not found")
                return False
        except Exception as e:
            logger.error(f"Error removing admin: {e}")
            return False

    def get_all_admins(self) -> List[Dict[str, Any]]:
        """Get all admins from the database."""
        if self._admins_collection is None:
            logger.error("Database connection not established")
            return []
        try:
            return list(self._admins_collection.find())
        except Exception as e:
            logger.error(f"Error getting all admins: {e}")
            return []

    #--------------------------------------------------------------------------
    # Settings and schedule management methods
    #--------------------------------------------------------------------------
    
    def get_schedule_settings(self) -> Dict[str, Any]:
        """Get the schedule settings."""
        if self._settings_collection is None:
            logger.error("Database connection not established")
            return {}
        try:
            settings = self._settings_collection.find_one({})
            if settings:
                return {
                    "daily_time": settings.get("daily_time", "09:00"),
                    "weekly_time": settings.get("weekly_time", "10:00"),
                    "weekly_day": settings.get("weekly_day", 1)
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting schedule settings: {e}")
            return {}

    def update_schedule_settings(
        self, daily_time: str = None, weekly_day: int = None, 
        weekly_time: str = None, daily_message: str = None, 
        weekly_message: str = None
    ) -> bool:
        """Update the schedule settings."""
        if self._settings_collection is None:
            logger.error("Database connection not established")
            return False
        try:
            update_data = {}
            if daily_time is not None:
                update_data["daily_time"] = daily_time
            if weekly_day is not None:
                update_data["weekly_day"] = weekly_day
            if weekly_time is not None:
                update_data["weekly_time"] = weekly_time
            
            # Update messages if provided
            if daily_message is not None or weekly_message is not None:
                # First get current messages
                settings = self._settings_collection.find_one({})
                messages = settings.get("messages", {}) if settings else {}
                
                if daily_message is not None:
                    messages["daily"] = daily_message
                if weekly_message is not None:
                    messages["weekly"] = weekly_message
                
                update_data["messages"] = messages
            
            if update_data:
                result = self._settings_collection.update_one({}, {"$set": update_data}, upsert=True)
                if result.modified_count > 0 or result.upserted_id:
                    logger.info(f"Updated schedule settings: {update_data}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error updating schedule settings: {e}")
            return False

    def get_announcement_messages(self) -> Dict[str, Any]:
        """Get the announcement messages."""
        if self._settings_collection is None:
            logger.error("Database connection not established")
            return {}
        try:
            settings = self._settings_collection.find_one({})
            if settings and "messages" in settings:
                return settings["messages"]
            return {}
        except Exception as e:
            logger.error(f"Error getting announcement messages: {e}")
            return {}

    def update_announcement_message(self, announcement_type: str, message: str) -> bool:
        """Update an announcement message."""
        if self._settings_collection is None:
            logger.error("Database connection not established")
            return False
        try:
            result = self._settings_collection.update_one(
                {}, 
                {"$set": {f"messages.{announcement_type}": message}}
            )
            if result.modified_count > 0:
                logger.info(f"Updated {announcement_type} announcement message")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating {announcement_type} announcement message: {e}")
            return False

    def check_connection(self) -> bool:
        """Check if the database connection is established and working."""
        if self._client is None or self._db is None:
            logger.error("❌ Database connection not established")
            return False
            
        try:
            # Try to ping the database
            self._client.admin.command('ping')
            logger.info("✅ Database connection is working")
            
            # Log collection information
            if self._users_collection is not None:
                user_count = self._users_collection.count_documents({})
                logger.info(f"📊 Users collection has {user_count} documents")
                
            if self._admins_collection is not None:
                admin_count = self._admins_collection.count_documents({})
                logger.info(f"📊 Admins collection has {admin_count} documents")
                
            if self._settings_collection is not None:
                settings_count = self._settings_collection.count_documents({})
                logger.info(f"📊 Settings collection has {settings_count} documents")
                
            return True
        except Exception as e:
            logger.error(f"❌ Database connection check failed: {e}")
            return False

# Create a singleton instance of the DatabaseManager
db_manager = DatabaseManager()
