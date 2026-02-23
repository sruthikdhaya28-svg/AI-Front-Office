"""
AI Handler for Google Gemini Integration
Handles intelligent conversations for the AI Front Office Manager
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import google.generativeai as genai

from config import Config

# Setup logging
logger = logging.getLogger(__name__)

# In-memory conversation storage (sufficient for MVP)
# For production, consider Redis or database
conversation_memory: Dict[str, List[Dict]] = {}


def initialize_gemini():
    """
    Initialize Gemini API with API key
    
    Raises:
        ValueError: If API key is not configured
    """
    if not Config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured in .env file")
    
    genai.configure(api_key=Config.GEMINI_API_KEY)
    logger.info(f"✅ Gemini initialized with model: {Config.AI_MODEL}")


def format_product_catalog(products: List[Dict]) -> str:
    """
    Format product catalog for AI context
    
    Args:
        products: List of product dictionaries from Google Sheets
    
    Returns:
        Formatted string with product information
    """
    if not products:
        return "No products available"
    
    catalog_text = "AVAILABLE PRODUCTS:\n"
    for product in products:
        name = product.get("Product_Name", "Unknown")
        unit_type = product.get("Unit_Type", "PIECE")
        price = product.get("Base_Price", "N/A")
        
        catalog_text += f"- {name} - ₹{price} per {unit_type.lower()}\n"
    
    return catalog_text


def create_system_prompt(products: List[Dict]) -> str:
    """
    Create comprehensive system prompt with product catalog
    
    Args:
        products: List of products from Google Sheets
    
    Returns:
        Complete system prompt for Gemini
    """
    product_catalog = format_product_catalog(products)
    
    system_prompt = f"""You are a friendly WhatsApp assistant for Anjali Sweets, a sweets and snacks shop in Tirunelveli, Tamil Nadu, India.

{product_catalog}

CONVERSATION RULES:
1. **ALWAYS respond in ENGLISH by default**
2. **Only switch to Tamil if customer writes MOSTLY in Tamil script (தமிழ்)**
   - Ignore Tamil slang words like "nga", "da", "venum" mixed with English
   - Example: "Hi nga" = English response (just slang)
   - Example: "வணக்கம் எனக்கு mysore pak venum" = Tamil response (mostly Tamil)
3. When a customer asks for a product:
   - Check if it's available in the catalog
   - Mention the product name, price, and unit (kg/piece/box)
   - Ask for quantity needed
4. When customer provides a quantity:
   - Understand quantities like "half kg", "250g", "ara", "quarter", "2 pieces", "1 box"
   - Calculate total price
   - Show the order summary
   - **Ask "Confirm pannalama sir?" or "Shall I confirm this order?"**
5. When customer confirms (says yes/confirm/ok/pannunga/ஆமா):
   - Acknowledge the confirmation
   - Tell them our team will inform preparation time shortly
6. Be concise, professional, and helpful
7. If you don't understand, politely ask for clarification

LANGUAGE SUPPORT:
- **Default: ALWAYS English** (even if customer uses Tamil slang words)
- Only use Tamil if customer writes FULL sentences in Tamil script
- Understand code-mixing but RESPOND in English

RESPONSE STYLE:
- Keep responses SHORT (1-2 sentences)
- Use "sir" or "madam" respectfully
- Use emojis sparingly (👍 ✅ only when confirming)
- Ask ONE question at a time
- Never make up products not in the catalog

IMPORTANT:
- Only discuss products from the AVAILABLE PRODUCTS list above
- If asked about a product not in list, say "Sorry sir, that product is not available right now"
- Always confirm quantity before considering order complete
- After quantity, ALWAYS ask if customer wants to confirm the order
- **RESPOND IN ENGLISH unless customer writes MOSTLY in Tamil script**"""
    
    return system_prompt


def get_conversation_history(phone: str) -> List[Dict]:
    """
    Get conversation history for a customer
    
    Args:
        phone: Customer phone number
    
    Returns:
        List of conversation messages (limited by MAX_CONVERSATION_HISTORY)
    """
    history = conversation_memory.get(phone, [])
    max_history = Config.MAX_CONVERSATION_HISTORY
    return history[-max_history:] if len(history) > max_history else history


def add_to_conversation_history(phone: str, role: str, message: str):
    """
    Add message to conversation history
    
    Args:
        phone: Customer phone number
        role: 'user' or 'assistant'
        message: Message text
    """
    if phone not in conversation_memory:
        conversation_memory[phone] = []
    
    conversation_memory[phone].append({
        "role": role,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })
    
    logger.debug(f"📝 Added to history ({phone}): {role} - {message[:50]}...")


def format_conversation_for_gemini(history: List[Dict], current_message: str) -> str:
    """
    Format conversation history for Gemini context
    
    Args:
        history: List of previous messages
        current_message: Current user message
    
    Returns:
        Formatted conversation string
    """
    if not history:
        return f"CUSTOMER MESSAGE: {current_message}"
    
    context = "RECENT CONVERSATION:\n"
    for msg in history[-5:]:  # Last 5 messages for context
        role = "Customer" if msg["role"] == "user" else "Assistant"
        context += f"{role}: {msg['message']}\n"
    
    context += f"\nNEW CUSTOMER MESSAGE: {current_message}"
    return context


def get_ai_response(
    phone: str, 
    user_message: str, 
    products: List[Dict],
    customer_context: Optional[Dict] = None
) -> str:
    """
    Get AI response from Gemini
    
    Args:
        phone: Customer phone number
        user_message: Customer's message
        products: Product catalog from Google Sheets
        customer_context: Optional context (existing leads, etc.)
    
    Returns:
        AI-generated response
    
    Raises:
        Exception: If Gemini API call fails
    """
    try:
        # Initialize Gemini if not already done
        initialize_gemini()
        
        # Get conversation history
        history = get_conversation_history(phone)
        
        # Create system prompt with products
        system_prompt = create_system_prompt(products)
        
        # Format conversation context
        conversation_context = format_conversation_for_gemini(history, user_message)
        
        # Add customer context if available
        if customer_context:
            context_info = f"\n\nCUSTOMER CONTEXT:\n{customer_context}"
            conversation_context += context_info
        
        # Combine system prompt and conversation
        full_prompt = f"{system_prompt}\n\n{conversation_context}\n\nRespond naturally and helpfully:"
        
        # Call Gemini API
        model = genai.GenerativeModel(Config.AI_MODEL)
        response = model.generate_content(full_prompt)
        
        ai_response = response.text.strip()
        
        # Add to conversation history
        add_to_conversation_history(phone, "user", user_message)
        add_to_conversation_history(phone, "assistant", ai_response)
        
        logger.info(f"🤖 AI Response ({phone}): {ai_response[:100]}...")
        
        return ai_response
        
    except Exception as e:
        logger.error(f"❌ Gemini API error: {e}", exc_info=True)
        raise


def extract_product_intent(
    ai_response: str, 
    user_message: str, 
    products: List[Dict]
) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Extract product and quantity from conversation
    
    Args:
        ai_response: AI's response
        user_message: User's message
        products: Product catalog
    
    Returns:
        Tuple of (list_of_matching_products, detected_quantity)
    """
    # Check if user message is purely numeric (likely quantity)
    if user_message.strip().isdigit():
        return None, user_message.strip()
    
    # Try to extract quantity from patterns like "10 rolls", "5 pieces", etc.
    import re
    detected_quantity = None
    
    # Tamil number words mapping
    tamil_numbers = {
        'onnu': '1', 'rendu': '2', 'moonu': '3', 'naalu': '4', 'ainthu': '5',
        'aaru': '6', 'ezhu': '7', 'ettu': '8', 'onpathu': '9', 'pathu': '10',
        'pathinonnu': '11', 'pannirandu': '12', 'patinaaru': '16', 'irupathu': '20',
        'muppathu': '30', 'narupathu': '40', 'aimpathu': '50', 'aruvathu': '60',
        'ezhupathu': '70', 'enampathu': '80', 'thonnooru': '90', 'nooru': '100'
    }
    
    # Check for Tamil number words
    message_lower = user_message.lower()
    for tamil_word, number in tamil_numbers.items():
        if tamil_word in message_lower:
            detected_quantity = number
            logger.info(f"🔢 Extracted Tamil quantity '{tamil_word}' = {number} from: '{user_message}'")
            break
    
    if not detected_quantity:
        quantity_patterns = [
            r'(\d+)\s*(rolls?|pieces?|units?|qty|quantity|numbers?)',
            r'(\d+)\s+(?:of\s+)?(?:the\s+)?'  # "10 of the", "5 the"
        ]
        for pattern in quantity_patterns:
            match = re.search(pattern, user_message.lower())
            if match:
                detected_quantity = match.group(1)
                logger.info(f"🔢 Extracted quantity {detected_quantity} from: '{user_message}'")
                break
    
    # Check if any product is mentioned in user's message ONLY
    # ✅ FIX: Do NOT check AI response - prevents AI echoing from creating duplicate leads
    user_lower = user_message.lower()
    
    matching_products = []
    for product in products:
        product_name = product.get("Product_Name", "").lower()
        
        # Only match products explicitly mentioned by the user
        if product_name in user_lower:
            matching_products.append(product)
            logger.info(f"🎯 Product '{product.get('Product_Name')}' matched in user message: '{user_message}'")
    
    if matching_products:
        if len(matching_products) == 1:
            logger.info(f"🎯 Product detected: {matching_products[0]['Product_Name']}")
        else:
            logger.info(f"⚠️ Multiple products matched ({len(matching_products)}): {[p['Product_Name'] for p in matching_products]}")
        return matching_products, detected_quantity
    
    # If no product found but quantity detected, return quantity only
    if detected_quantity:
        return None, detected_quantity
    
    return None, None


def extract_structured_data(user_message: str, products: List[Dict]) -> Dict[str, Any]:
    """
    Extract structured information from user message using Gemini JSON mode
    
    Returns:
        Dict containing:
        - product_detected: str (Name from catalog or null)
        - quantity_detected: int/str (Value or null)
        - intent: str (enquiry, confirmation, cancellation, greeting, other)
        - language: str (en, ta, hi)
    """
    try:
        initialize_gemini()
        
        product_names = [p.get("Product_Name") for p in products]
        
        extraction_prompt = f"""
        Analyze this customer message for Anjali Sweets (a sweets and snacks shop).
        Available Products: {', '.join(product_names)}
        
        CUSTOMER MESSAGE: "{user_message}"
        
        Extract information into JSON format with these exact keys:
        - product_detected: Match the customer's request to a product from the list above. 
          IMPORTANT: 
          * If customer says partial name (e.g., "pak", "laddu", "murukku"), find the matching product from the list
          * "pak" → "Mysore Pak" or "Special Mysore Pak" (choose most common)
          * "laddu" → "Laddu"  
          * "mixture" → "Mixture" or "Special Mixture"
          * If multiple products mentioned, return ONLY THE FIRST ONE
          * Return exact Product_Name from list, or null if no match
        - quantity_detected: The number of units asked for. Convert words like 'half', 'ara', 'quarter', '250g' to appropriate values. If not mentioned, null.
        - intent: One of [enquiry, confirmation, cancellation, greeting, catalog, other]. 
            - 'confirmation' is for yes/ok/confirm/pannunga/pannidu/sari/podunga.
            - 'cancellation' is for no/cancel/wait.
            - 'catalog' is for "what sweets do you have", "show menu", "list items", "what all available", "what products", "tell me items".
        - language: 'en', 'ta', or 'hi'.
        
        Return ONLY valid JSON.
        """
        
        model = genai.GenerativeModel(Config.AI_MODEL)
        response = model.generate_content(
            extraction_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        data = json.loads(response.text)
        logger.info(f"📊 Extracted Data: {data}")
        return data
        
    except Exception as e:
        logger.error(f"❌ Extraction error: {e}")
        return {
            "product_detected": None,
            "quantity_detected": None,
            "intent": "other",
            "language": "en"
        }


def get_fallback_response(intent: str) -> str:
    """Get a simple fallback response if AI fails"""
    responses = {
        "greeting": "Hello! How can I help you with sweets today?",
        "enquiry": "I'm sorry, could you please tell me which sweet and how much quantity you need?",
        "other": "I'm not sure I understood. Could you please clarify?"
    }
    return responses.get(intent, "How can I help you today?")


def clear_conversation_history(phone: str):
    """
    Clear conversation history for a customer
    
    Args:
        phone: Customer phone number
    """
    if phone in conversation_memory:
        del conversation_memory[phone]
        logger.info(f"🗑️ Cleared conversation history for {phone}")


def detect_confirmation_intent(user_message: str) -> Optional[str]:
    """
    Detect if customer is confirming or canceling the order
    
    Args:
        user_message: Customer's message
    
    Returns:
        'CONFIRMED' if customer confirms
        'CANCELLED' if customer cancels
        None if unclear
    """
    message_lower = user_message.lower().strip()
    
    # STEP 1: Reject messages that contain questions or question words
    question_indicators = ['?', 'what', 'where', 'how', 'which', 'why']
    for indicator in question_indicators:
        if indicator in message_lower:
            logger.info(f"❓ Looks like a question, not a confirmation: '{user_message}'")
            return None
    
    # STEP 2: Define keywords (English, Tamil, Hindi)
    confirm_keywords = [
        # English
        'yes', 'ok', 'okay', 'confirm', 'sure', 'proceed', 'go ahead', 'done', 'fine',
        # Tamil (Script)
        'ஆமா', 'சரி', 'போடு', 'வேணும்', 'சரியான', 'உறுதி',
        # Tamil (Tanglish)
        'pannidu', 'pannunga', 'pannu', 'podu', 'kudunga', 'anuppuga',
        'sari', 'ama', 'aama', 'amam', 'ok nga', 'ok da', 'done nga',
        'confirm pannidu', 'confirm pannunga', 'confirm pannu',
        # Hindi
        'हाँ', 'हां', 'ठीक', 'theek', 'haan', 'ha', 'accha', 'karo'
    ]
    
    cancel_keywords = [
        # English
        'no', 'cancel', 'not', 'later', 'wait', 'stop',
        # Tamil (Script)
        'வேண்டாம்', 'இல்ல', 'பின்ன', 'காத்திரு', 'நிறுத்து',
        # Tamil (Tanglish)
        'vendaam', 'venam', 'illa', 'illai', 'wait pannunga', 'wait panunga',
        'cancel pannidu', 'cancel pannunga', 'apram', 'sapptu solren',
        # Hindi
        'नहीं', 'नही', 'mat', 'ruko', 'nahi', 'mat', 'ruko'
    ]
    
    # STEP 3: Message must be SHORT (< 10 words) to be a clear confirmation/cancellation
    words = message_lower.split()
    if len(words) > 10:
        logger.info(f"❓ Message too long ({len(words)} words) for confirmation: '{user_message}'")
        return None
    
    # STEP 4 & 5: Check for keywords using word boundaries to avoid false matches (like 'mat' in 'information')
    import re
    
    for keyword in confirm_keywords:
        pattern = rf'\b{re.escape(keyword)}\b'
        if re.search(pattern, message_lower):
            logger.info(f"✅ Detected confirmation: '{user_message}'")
            return 'CONFIRMED'
    
    for keyword in cancel_keywords:
        pattern = rf'\b{re.escape(keyword)}\b'
        if re.search(pattern, message_lower):
            logger.info(f"❌ Detected cancellation: '{user_message}'")
            return 'CANCELLED'
    
    logger.info(f"❓ No clear confirmation/cancellation detected in: '{user_message}'")
    return None


def get_fallback_response() -> str:
    """
    Get fallback response when AI fails
    
    Returns:
        Generic helpful message
    """
    return (
        "Welcome to Anjali Sweets! 🙏 "
        "Please tell me which sweet or snack you need. "
        "For example: Mysore Pak, Laddu, Murukku, Mixture, etc."
    )
