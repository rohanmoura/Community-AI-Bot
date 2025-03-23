# This file will handle AI responses using OpenRouter API for Google Gemini

import os
import logging
import requests
import json
from dotenv import load_dotenv

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure the OpenRouter API
api_key = os.getenv("OPENROUTER_API_KEY")
site_url = os.getenv("SITE_URL", "")
site_name = os.getenv("SITE_NAME", "")

if not api_key:
    logger.error("No OPENROUTER_API_KEY found in environment variables!")

# Define which model to use via OpenRouter
MODEL_NAME = 'google/gemini-2.0-pro-exp-02-05:free'  # Using Gemini Pro via OpenRouter

# Define the system message for community management context
SYSTEM_MESSAGE = """You are a Community Management Assistant for a Telegram bot serving a community focused on Systemic Altruism. 
Your responses should be friendly, informative, and centered around community engagement, including onboarding, FAQs, event updates, and announcements. 
Avoid generic problem-solving unless it directly relates to community management.
Keep your responses concise and helpful for community members."""

async def generate_ai_response(user_message: str) -> str:
    """
    Get an AI-generated response using OpenRouter API for Google Gemini.
    
    Args:
        user_message: The message from the user
        
    Returns:
        AI-generated response as a string or fallback message if API fails
    """
    if not api_key:
        logger.error("Missing OpenRouter API key - cannot generate AI response")
        return "Sorry, AI service is currently unavailable due to configuration issues."
    
    try:
        # Set up the headers for OpenRouter API
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Add optional headers if provided in environment variables
        if site_url:
            headers["HTTP-Referer"] = site_url
        if site_name:
            headers["X-Title"] = site_name
        
        # Prepare the request payload with system message for context
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_MESSAGE
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message
                        }
                    ]
                }
            ]
        }
        
        # Make the API request to OpenRouter
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the response
        response_json = response.json()
        
        # Extract the AI-generated text from the response
        ai_text = response_json["choices"][0]["message"]["content"]
        
        return ai_text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making request to OpenRouter API: {e}")
        return "I'm having trouble connecting to my AI brain right now. Please try again in a moment or contact the admin if this persists."
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing OpenRouter API response: {e}")
        return "I received an unexpected response format. Please try again or contact the admin."
    except Exception as e:
        logger.error(f"Unexpected error generating AI response: {e}")
        return "I'm having trouble processing your request right now. Please try again in a moment."