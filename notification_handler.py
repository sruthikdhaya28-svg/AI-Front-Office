"""
Notification Handler for Order Confirmations
Sends Telegram notifications to shop owner when orders are confirmed
"""
import logging
import requests
from typing import Dict, Optional
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)


def send_telegram_notification(order_details: Dict) -> bool:
    """
    Send notification via Telegram
    
    Args:
        order_details: Order details dictionary
        
    Returns:
        True if sent successfully, False otherwise
    """
    import time
    
    bot_token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID
    
    if not bot_token or not chat_id:
        logger.error("❌ Telegram credentials not configured")
        return False
    
    # Format message
    message = format_order_notification(order_details)
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    # Retry logic with exponential backoff
    max_retries = 3
    timeout = 15  # Increased from 10
    
    for attempt in range(max_retries):
        try:
            logger.info(f"📤 Sending Telegram notification (attempt {attempt + 1}/{max_retries})")
            response = requests.post(url, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                logger.info(f"✅ Telegram notification sent for order")
                return True
            else:
                logger.error(f"❌ Telegram notification failed: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Telegram timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.info(f"⏳ Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ Telegram notification failed after {max_retries} attempts")
                
        except Exception as e:
            logger.error(f"❌ Error sending Telegram notification: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
    
    return False


def format_order_notification(order: Dict) -> str:
    """
    Format order details into notification message
    
    Args:
        order: Order details dictionary
        
    Returns:
        Formatted notification message
    """
    # Extract order details
    customer_name = order.get("Customer_Name", "Unknown")
    phone = str(order.get("Phone", "N/A"))  # Convert to string first!
    product_name = order.get("Product_Name", "Unknown Product")
    quantity = order.get("Quantity_Asked", "0")
    price = order.get("Price_Shown", "0")
    # Always show CONFIRMED since this function is only called on confirmation
    status = "CONFIRMED"
    
    # Calculate total
    try:
        total = round(float(price) * float(quantity), 2)
    except:
        total = 0
    
    # Get current time
    now = datetime.now()
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%d %b %Y")
    
    # Format WhatsApp link
    phone_clean = phone.replace("+", "").replace("-", "").replace(" ", "")
    wa_link = f"https://wa.me/{phone_clean}"
    
    # Build message
    message = f"""🎉 <b>NEW ORDER {status}!</b>

👤 <b>Customer:</b> {customer_name}
📞 <b>Phone:</b> {phone}

📦 <b>ORDER DETAILS:</b>
Product: {product_name}
Quantity: {quantity}
Price: ₹{price} each
💰 <b>Total: ₹{total}</b>

✅ <b>Status:</b> {status}
🕐 <b>Time:</b> {time_str}, {date_str}

📞 <b>Contact customer:</b> {wa_link}"""
    
    return message


def notify_owner(order_details: Dict) -> bool:
    """
    Main function to notify owner about order
    Currently uses Telegram, can be extended for other channels
    
    Args:
        order_details: Order information
        
    Returns:
        True if notification sent successfully
    """
    logger.info(f"📢 Sending owner notification for order")
    
    # Send via Telegram
    success = send_telegram_notification(order_details)
    
    if success:
        logger.info("✅ Owner notified successfully")
    else:
        logger.warning("⚠️ Owner notification failed")
    
    return success
