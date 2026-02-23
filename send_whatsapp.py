"""
WhatsApp Cloud API integration for sending messages
"""
import requests
import logging
from typing import Tuple, Dict

from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_whatsapp_message(to_number: str, message_text: str) -> Tuple[int, Dict]:
    """
    Send a WhatsApp message using the Cloud API
    
    Args:
        to_number: Recipient phone number (with country code, no +)
        message_text: Message text to send
    
    Returns:
        Tuple of (status_code, response_json)
    """
    url = f"https://graph.facebook.com/v22.0/{Config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {Config.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text},
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ Message sent to {to_number}")
        else:
            logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
        
        return response.status_code, response.json()
        
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp message: {e}")
        return 500, {"error": str(e)}

