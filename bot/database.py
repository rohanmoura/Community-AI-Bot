# This file handles storing user data, chat logs, and interactions in MongoDB.

import os
import logging
import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class DatabaseManager:
    _instance = None
    _client = None
    _db = None
    _users_collection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._connect_to_db()
        return cls._instance
    
    @classmethod
    def _connect_to_db(cls) -> None:
        """Connect to MongoDB using the URI from environment variables."""
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            logger.error("No MONGODB_URI found in environment variables!")
            return
        
        try:
            cls._client = MongoClient(mongodb_uri)
            cls._db = cls._client.get_database("telegram_bot")
            cls._users_collection = cls._db.get_collection("users")
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a user by their Telegram user ID."""
        if self._users_collection is None:
            logger.error("Database connection not established")
            return None
        
        return self._users_collection.find_one({"user_id": user_id})
    
    def add_user(self, user_data: Dict[str, Any]) -> bool:
        """Add a new user to the database."""
        if self._users_collection is None:
            logger.error("Database connection not established")
            return False
        
        try:
            # Check if user already exists
            existing_user = self.get_user(user_data["user_id"])
            if existing_user:
                logger.info(f"User {user_data['user_id']} already exists in database")
                return True
            
            # Initialize empty messages array
            user_data["messages"] = []
            
            # Insert the new user
            self._users_collection.insert_one(user_data)
            logger.info(f"Added new user {user_data['user_id']} to database")
            return True
        except Exception as e:
            logger.error(f"Failed to add user to database: {e}")
            return False
    
    def add_message(self, user_id: int, message_text: str) -> bool:
        """Add a message to a user's message history."""
        if self._users_collection is None:
            logger.error("Database connection not established")
            return False
        
        try:
            # Create message object
            message = {
                "text": message_text,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
            
            # Add message to user's messages array
            result = self._users_collection.update_one(
                {"user_id": user_id},
                {"$push": {"messages": message}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Added message for user {user_id}")
                return True
            else:
                logger.warning(f"Failed to add message for user {user_id}")
                return False
        except Exception as e:
            logger.error(f"Error adding message to database: {e}")
            return False

# Create a singleton instance
db_manager = DatabaseManager()