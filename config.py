"""
Configuration management for AI Front Office Manager
Loads environment variables and validates required configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""
    
    # WhatsApp API Configuration
    WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "my_verify_token_123")
    
    # Google Sheets Configuration
    GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Anjali_Sweets")
    
    # Application Configuration
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    
    # Business Logic Configuration
    DEFAULT_REMINDERS = int(os.getenv("DEFAULT_REMINDERS", "3"))
    DAYS_BEFORE_REMINDER = int(os.getenv("DAYS_BEFORE_REMINDER", "2"))
    
    # Google Gemini AI Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    USE_AI_MODE = os.getenv("USE_AI_MODE", "False").lower() == "true"
    AI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash-exp")
    MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Shop Information (Anjali Sweets)
    SHOP_NAME = os.getenv("SHOP_NAME", "Anjali Sweets")
    SHOP_TIMING = os.getenv("SHOP_TIMING", "8 AM - 9 PM")
    SHOP_LOCATION = os.getenv("SHOP_LOCATION", "Adambakkam, Chennai")
    DELIVERY_INFO = os.getenv("DELIVERY_INFO", "Delivery available within 5 km")

    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        required = [
            ("WHATSAPP_ACCESS_TOKEN", cls.WHATSAPP_ACCESS_TOKEN),
            ("WHATSAPP_PHONE_NUMBER_ID", cls.WHATSAPP_PHONE_NUMBER_ID),
            ("WEBHOOK_VERIFY_TOKEN", cls.WEBHOOK_VERIFY_TOKEN),
            ("GOOGLE_CREDENTIALS_FILE", cls.GOOGLE_CREDENTIALS_FILE),
        ]
        
        missing = []
        for name, value in required:
            if not value:
                missing.append(name)
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True


# Validate configuration on import
Config.validate()
