"""
WhatsApp Webhook Server for AI Front Office Manager
Handles incoming messages, manages conversation state, and captures leads

v2 - Architecture Fix:
  - 3-state session machine (IDLE → WAITING_QUANTITY → WAITING_CONFIRMATION)
  - No early lead creation (only write to sheet on confirmation)
  - Deterministic reply templates (English + Tamil-mixed)
  - 3-level product matching (exact → word-boundary → fuzzy)
  - Catalog/menu intent handler
  - AI used only for intent/language extraction
"""
from flask import Flask, request, render_template
import logging
from datetime import datetime
from typing import Optional, Dict

from config import Config
from sheets_manager import get_sheets_manager
from send_whatsapp import send_whatsapp_message
from ai_handler import extract_structured_data, detect_confirmation_intent
from notification_handler import notify_owner
from utils import (
    extract_quantity,
    resolve_product,
    get_shop_info_response,
    format_quantity_with_unit
)

# Setup logging with UTF-8 support for Windows
import sys
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
log_level = logging.DEBUG if Config.DEBUG_MODE else logging.INFO

# Explicitly create handlers with UTF-8 encoding
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_level)
console_handler.setFormatter(logging.Formatter(log_format))

file_handler = logging.FileHandler('webhook_demo.log', encoding='utf-8')
file_handler.setLevel(log_level)
file_handler.setFormatter(logging.Formatter(log_format))

logging.basicConfig(
    level=log_level,
    handlers=[console_handler, file_handler]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Register admin blueprint
from admin_routes import admin_bp
app.register_blueprint(admin_bp)

# Initialize Google Sheets Manager
sheets = get_sheets_manager()

# ==================== SESSION STATE MACHINE ====================
# States: IDLE → WAITING_QUANTITY → WAITING_CONFIRMATION
# Session holds ALL order data in memory until confirmation.
# NO sheet writes until confirmation.

session_store: Dict[str, dict] = {}
# Structure per phone:
# {
#     "state": "IDLE" | "WAITING_QUANTITY" | "WAITING_CONFIRMATION",
#     "product": { ... },        # full product dict from STOCK_MASTER
#     "quantity": None,           # float (set when quantity parsed)
#     "total": None,              # float (set when calculated)
#     "language": "en",           # "en" or "ta"
# }

# Message deduplication cache
processed_messages = {}
MESSAGE_CACHE_DURATION = 300  # 5 minutes

logger.info("🚀 WhatsApp Webhook Server Starting (v2 - Architecture Fix)...")
logger.info(f"📦 Products loaded: {len(sheets.get_products())}")
logger.info(f"🔑 Keywords indexed: {len(sheets.get_keyword_map())}")


# ==================== REPLY TEMPLATES ====================

TEMPLATES = {
    "en": {
        "greeting": "Good {time_period} sir/Madam! 🙏 Welcome to {shop_name}. How can I help you today? You can ask about our sweets, timings, or place an order!",
        "product_found": "{product_name} is available.\nPrice ₹{price} per {unit}.\nHow many {unit_plural} would you like?",
        "quantity_confirm": "Noted {quantity} {unit}.\nTotal ₹{total}.\nShall I confirm the order?",
        "order_confirmed": "Order confirmed 👍\nWe will prepare it. Our team will inform you the preparation time shortly! 🙏",
        "order_cancelled": "Okay sir, I have cancelled that order. How else can I help you?",
        "disambiguation": "Sir, I found multiple products matching your request. Which one do you need?\n\n{options}\n\nPlease reply with the exact product name.",
        "product_not_found": "Sorry sir, I couldn't find that product in our catalog. Please check our menu or try again.",
        "catalog_header": "Here are our products:\n\n{product_list}\n\nWhich product would you like to order?",
        "already_waiting_qty": "Sir, we are waiting for quantity for {product_name}.\nPrice: ₹{price} per {unit}.\nHow many {unit_plural} do you need?",
        "invalid_quantity": "Sorry sir, I couldn't understand the quantity. Please enter a number like 1, 2, 0.5, 250g, or half.",
        "no_pending_order": "Please tell me which product you need first.",
        "multi_items": "Sorry sir, multiple items in one order is not supported. 🙏\nKindly order one product at a time.\nWhich product would you like to order first?",
        "cancel_confirm": "No problem sir! What would you like to change? 😊\n\nCurrent order: *{product_name}*{quantity_line}{unit}\n\nReply with:\n• New quantity (e.g. '10')\n• Different product name\n• *Cancel* to remove this order",
    },
    "ta": {
        "greeting": "Vanakkam sir! 🙏 {shop_name} la welcome. Enna venum sir? Sweets, snacks, timing, order - ellaame sollunga!",
        "product_found": "Yes sir/Madam, {product_name} available.\nPrice ₹{price} per {unit}.\nEvlo {unit_plural} venum sir?",
        "quantity_confirm": "Noted {quantity} {unit}.\nTotal ₹{total}.\nConfirm pannalama sir?",
        "order_confirmed": "Order confirmed sir 👍\nPrepare pannidrom. Our team will inform you shortly! 🙏",
        "order_cancelled": "Sari sir, order cancel pannittom. Vera enna venum?",
        "disambiguation": "Sir, inga paarunga - multiple items match aaguthu. Ethavadhu oru specific item sollunga:\n\n{options}\n\nExact name reply pannunga sir.",
        "product_not_found": "Sorry sir, antha product engala catalog la illa. Menu paarunga or try again pannunga.",
        "catalog_header": "Enga products:\n\n{product_list}\n\nEtha order panna venum sir?",
        "already_waiting_qty": "Sir, {product_name} ku quantity sollunga.\nPrice: ₹{price} per {unit}.\nEvlo {unit_plural} venum?",
        "invalid_quantity": "Sorry sir, quantity puriyala. 1, 2, 0.5, 250g, or half nu sollunga.",
        "no_pending_order": "Sir, mudhalil enna product venum nu sollunga.",
        "multi_items": "Sorry sir, oru neram oru product mattum order panna mudiyum. 🙏\nMudhalil etha product venum nu sollunga sir.",
        "cancel_confirm": "Paravala sir! Enna maathanum? 😊\n\nCurrent order: *{product_name}*{quantity_line}\n\nReply pannunga:\n• Pudhusu quantity (e.g. '10')\n• Vera product name\n• *Cancel* nu type pannunga remove panna",
    }
}


# ==================== LANGUAGE DETECTION ====================

TAMIL_INDICATORS = [
    "venum", "iruka", "evlo", "sollunga", "kudunga", "pannunga",
    "podhum", "vendaam", "sari", "illa", "enna", "enga",
    "inga", "anga", "atha", "itha", "ara", "kaal", "nga",
    "da", "la", "ah", "eh", "enakku", "podu",
]


def detect_language(text: str, ai_language: str = "en") -> str:
    """
    Detect if user is speaking English or Tamil-mixed.
    
    Rule: If AI says 'ta' OR if message contains Tamil indicator words → Tamil.
    Otherwise → English.
    """
    text_lower = text.lower()
    
    # Check for Tamil indicator words
    for word in TAMIL_INDICATORS:
        # Use word boundary to avoid false positives
        if f" {word} " in f" {text_lower} " or text_lower.startswith(word + " ") or text_lower.endswith(" " + word) or text_lower == word:
            return "ta"
    
    # Trust AI language detection for Tamil
    if ai_language == "ta":
        return "ta"
    
    return "en"


# ==================== HELPER FUNCTIONS ====================

def get_session(phone: str) -> dict:
    """Get or create session for a phone number."""
    if phone not in session_store:
        session_store[phone] = {
            "state": "IDLE",
            "product": None,
            "quantity": None,
            "total": None,
            "language": "en",
            "lead_id": None,
        }
    return session_store[phone]


def clear_session(phone: str):
    """Clear session after order completion or cancellation."""
    if phone in session_store:
        del session_store[phone]
        logger.info(f"🗑️ Session cleared for {phone}")


def get_template(lang: str, key: str) -> str:
    """Get reply template for language and key."""
    return TEMPLATES.get(lang, TEMPLATES["en"]).get(key, TEMPLATES["en"].get(key, ""))


def get_unit_info(product: dict) -> tuple:
    """Get unit and unit_plural from product."""
    unit_type = product.get("Unit_Type", "PIECE").upper()
    unit_map = {
        "KG": ("kg", "kg"),
        "PIECE": ("piece", "pieces"),
        "BOX": ("box", "boxes"),
    }
    return unit_map.get(unit_type, ("unit", "units"))


def handle_greeting(lang: str) -> str:
    """Generate greeting response."""
    hour = datetime.now().hour
    if hour < 12:
        time_period = "morning"
    elif hour < 17:
        time_period = "afternoon"
    else:
        time_period = "evening"
    
    return get_template(lang, "greeting").format(
        time_period=time_period,
        shop_name=Config.SHOP_NAME
    )


def handle_catalog(lang: str, products: list) -> str:
    """Generate catalog/menu response."""
    # Group by Unit_Type
    by_unit = {}
    for p in products:
        unit = p.get("Unit_Type", "PIECE").upper()
        if unit not in by_unit:
            by_unit[unit] = []
        by_unit[unit].append(p)
    
    lines = []
    unit_labels = {"KG": "Per KG", "PIECE": "Per Piece", "BOX": "Per Box"}
    
    for unit_type, prods in by_unit.items():
        label = unit_labels.get(unit_type, unit_type)
        lines.append(f"📦 *{label}:*")
        for p in prods:
            name = p.get("Product_Name", "")
            price = p.get("Base_Price", "")
            lines.append(f"  • {name} – ₹{price}")
        lines.append("")  # blank line between groups
    
    product_list = "\n".join(lines).strip()
    return get_template(lang, "catalog_header").format(product_list=product_list)


def is_catalog_intent(text: str, ai_intent: str) -> bool:
    """Check if user wants to see the catalog/menu."""
    if ai_intent == "catalog":
        return True
    
    catalog_keywords = [
        "what sweets", "what snacks", "list items", "show menu",
        "what all available", "menu", "what do you have",
        "what products", "tell me items", "full list",
        "all products", "all items", "everything you have",
        "complete list", "all of them", "everything",
        "what all", "enna iruku", "enna enna iruku",
        "enna venum", "items enna",
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in catalog_keywords)


def is_greeting(text: str) -> bool:
    """Check if message is a greeting."""
    import re
    greetings = ["hi", "hello", "hey", "good morning", "good evening",
                  "good afternoon", "vanakkam", "namaste"]
    text_lower = text.lower().strip()
    
    # Must be short (greeting only)
    words = text_lower.split()
    if len(words) <= 3:
        for g in greetings:
            # Build word-boundary regex: \bword\b
            pattern = r'\b' + re.escape(g) + r'\b'
            if re.search(pattern, text_lower):
                return True
    return False


def is_confirmation(text: str, ai_intent: str) -> bool:
    """Check if user is confirming the order."""
    if ai_intent == "confirmation":
        return True
    result = detect_confirmation_intent(text)
    return result == "CONFIRMED"


def is_hard_cancel(text: str) -> bool:
    """Check if user explicitly typed 'cancel' — triggers actual cancellation."""
    import re
    return bool(re.search(r'\bcancel\b', text.lower()))


def is_soft_cancel(text: str, ai_intent: str) -> bool:
    """Check if user shows cancellation intent (no/wait/don't) — triggers confirmation prompt."""
    if ai_intent == "cancellation":
        return True
    result = detect_confirmation_intent(text)
    return result == "CANCELLED"


def detect_multiple_products(text: str, products: list) -> list:
    """
    Detect if user mentions multiple distinct products in a single message.
    Splits by connectors (and, &, comma) and tries to resolve each segment.
    Returns list of matched product names (empty or 1 = safe, 2+ = multi-item).
    """
    import re
    
    # Split by common connectors: "and", "&", ",", "+"
    # Also handle Tamil connectors: "um", "maattum"
    segments = re.split(r'\band\b|&|,|\+|\bum\b|\bmaattum\b', text, flags=re.IGNORECASE)
    
    # Clean segments and filter out empty/very short ones
    segments = [s.strip() for s in segments if s.strip() and len(s.strip()) > 1]
    
    # If there's only one segment, no multi-product possible from connectors
    if len(segments) <= 1:
        return []
    
    # Try to resolve each segment as a product
    matched_products = []
    seen_ids = set()
    
    for segment in segments:
        # Strip common conversational prefixes
        cleaned = re.sub(r'^(i\s+want|i\s+need|give\s+me|get\s+me|venum|thaa)\s+', '', segment.strip(), flags=re.IGNORECASE).strip()
        if not cleaned or len(cleaned) < 2:
            continue
            
        product, candidates = resolve_product(cleaned, products)
        if product:
            pid = product.get("Product_ID", "")
            if pid not in seen_ids:
                matched_products.append(product.get("Product_Name", ""))
                seen_ids.add(pid)
        elif candidates:
            # Even if ambiguous, it means this segment refers to some product(s)
            pid = candidates[0].get("Product_ID", "")
            if pid not in seen_ids:
                matched_products.append(candidates[0].get("Product_Name", "") + " (ambiguous)")
                seen_ids.add(pid)
    
    return matched_products


# ==================== ADMIN DASHBOARD ====================

@app.route("/admin")
def admin_dashboard():
    """Serve the admin dashboard"""
    return render_template("admin_dashboard.html")


# ==================== WEBHOOK ENDPOINTS ====================

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """
    Main webhook endpoint for WhatsApp Cloud API
    
    GET: Verification (Meta requirement)
    POST: Incoming messages
    """
    
    # ========== VERIFICATION (GET) ==========
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode == "subscribe" and token == Config.WEBHOOK_VERIFY_TOKEN:
            logger.info("✅ Webhook verified successfully")
            return challenge, 200
        else:
            logger.warning("❌ Webhook verification failed")
            return "Forbidden", 403
    
    # ========== INCOMING MESSAGE (POST) ==========
    data = request.get_json()
    logger.debug(f"📥 Webhook data: {data}")
    
    try:
        # Parse WhatsApp webhook payload
        entry = data.get("entry", [])
        if not entry:
            return "EVENT_RECEIVED", 200
        
        changes = entry[0].get("changes", [])
        if not changes:
            return "EVENT_RECEIVED", 200
        
        value = changes[0].get("value", {})
        
        if "messages" not in value:
            return "EVENT_RECEIVED", 200
        
        messages = value.get("messages", [])
        if not messages:
            return "EVENT_RECEIVED", 200
        
        # Extract message details
        message = messages[0]
        message_id = message.get("id")
        phone = message.get("from")
        
        # ✅ MESSAGE DEDUPLICATION
        import time
        import hashlib
        current_time = time.time()
        
        dedup_key = message_id if message_id else hashlib.md5(
            f"{phone}:{int(current_time / 2)}".encode()
        ).hexdigest()
        
        # Clean old entries
        expired = [k for k, ts in processed_messages.items() if current_time - ts > MESSAGE_CACHE_DURATION]
        for k in expired:
            del processed_messages[k]
        
        if dedup_key in processed_messages:
            logger.warning(f"⏭️ DUPLICATE message {dedup_key} - skipping")
            return "EVENT_RECEIVED", 200
        
        processed_messages[dedup_key] = current_time
        
        # Only handle text messages
        if "text" not in message:
            send_whatsapp_message(phone, "Please send text messages for now. Image support coming soon!")
            return "EVENT_RECEIVED", 200
        
        text = message["text"]["body"].strip()
        logger.info(f"📨 Message from {phone}: {text}")
        
        # ========== GET SESSION & PRODUCTS ==========
        session = get_session(phone)
        products = sheets.get_products()
        
        # ========== SHOP INFO QUERIES (HANDLE FIRST) ==========
        shop_keywords = ['timing', 'time', 'open', 'close', 'location', 'address', 'where', 'delivery', 'deliver']
        if any(keyword in text.lower() for keyword in shop_keywords):
            reply = get_shop_info_response(text)
            send_whatsapp_message(phone, reply)
            return "EVENT_RECEIVED", 200
        
        # ========== AI EXTRACTION (intent + language) ==========
        extracted = extract_structured_data(text, products)
        ai_intent = extracted.get("intent", "other")
        ai_language = extracted.get("language", "en")
        lang = detect_language(text, ai_language)
        session["language"] = lang
        
        # ========== CATALOG HANDLER ==========
        if is_catalog_intent(text, ai_intent):
            reply = handle_catalog(lang, products)
            send_whatsapp_message(phone, reply)
            return "EVENT_RECEIVED", 200
        
        # ========== 3-STATE MACHINE ==========
        reply = ""
        state = session["state"]
        
        # ----- STATE: IDLE -----
        if state == "IDLE":
            if is_greeting(text):
                reply = handle_greeting(lang)
            else:
                # Check for multiple products in a single message
                multi_products = detect_multiple_products(text, products)
                if len(multi_products) >= 2:
                    reply = get_template(lang, "multi_items")
                    logger.info(f"⚠️ Multiple products detected: {multi_products} — asking customer to order one at a time")
                else:
                    # Try to detect a product
                    product, candidates = resolve_product(text, products)
                
                    # If resolve_product didn't find anything, try AI's product detection as fallback
                    if not product and not candidates:
                        ai_product_name = extracted.get("product_detected")
                        if ai_product_name:
                            # Handle AI returning list or comma-separated
                            if isinstance(ai_product_name, list):
                                ai_product_name = ai_product_name[0] if ai_product_name else None
                            elif isinstance(ai_product_name, str) and "," in ai_product_name:
                                ai_product_name = ai_product_name.split(",")[0].strip()
                            
                            if ai_product_name:
                                # Try to find this product in our catalog
                                product = next((p for p in products if p["Product_Name"].lower() == ai_product_name.lower()), None)
                                if product:
                                    logger.info(f"🤖 AI fallback matched: {product['Product_Name']}")
                
                    if product:
                        # Single match → store in session, ask quantity
                        session["product"] = product
                        session["state"] = "WAITING_QUANTITY"
                        
                        # Create ACTIVE lead in LEADS_ACTIVE sheet
                        lead_id = sheets.create_active_lead(phone, product)
                        session["lead_id"] = lead_id
                        
                        unit, unit_plural = get_unit_info(product)
                        reply = get_template(lang, "product_found").format(
                            product_name=product["Product_Name"],
                            price=product.get("Base_Price", ""),
                            unit=unit,
                            unit_plural=unit_plural
                        )
                        logger.info(f"✅ Product stored in session: {product['Product_Name']}, lead_id={lead_id}, state → WAITING_QUANTITY")
                        
                    elif candidates:
                        # Multiple matches → ask clarification
                        options = "\n".join([f"  {i+1}. {p['Product_Name']}" for i, p in enumerate(candidates)])
                        reply = get_template(lang, "disambiguation").format(options=options)
                        logger.info(f"🔢 Disambiguation: {len(candidates)} candidates shown")
                        
                    else:
                        # Nothing found
                        if ai_intent == "greeting":
                            reply = handle_greeting(lang)
                        else:
                            reply = get_template(lang, "product_not_found")
        
        # ----- STATE: WAITING_QUANTITY -----
        elif state == "WAITING_QUANTITY":
            product = session["product"]
            unit_type = product.get("Unit_Type", "PIECE").upper()
            unit, unit_plural = get_unit_info(product)
            
            # Check for hard cancel (explicit 'cancel') first
            if is_hard_cancel(text):
                # Update ACTIVE lead to CANCELLED in LEADS_ACTIVE
                if session.get("lead_id"):
                    sheets.cancel_active_lead(session["lead_id"])
                clear_session(phone)
                reply = get_template(lang, "order_cancelled")
            
            # Check for soft cancel signals (no/wait/don't) → ask confirmation
            elif is_soft_cancel(text, ai_intent):
                qty_info = f", Quantity: {session.get('quantity')}" if session.get('quantity') else ""
                unit, unit_plural = get_unit_info(product)
                reply = get_template(lang, "cancel_confirm").format(
                    product_name=product.get("Product_Name", ""),
                    quantity_line=qty_info,
                    unit=unit
                )
                logger.info(f"⚠️ Soft cancel detected, asking for confirmation")
            
            # Check if user wants a different product (restart)
            elif ai_intent == "enquiry":
                new_product, new_candidates = resolve_product(text, products)
                if new_product and new_product.get("Product_Name") != product.get("Product_Name"):
                    # User switched product
                    session["product"] = new_product
                    session["quantity"] = None
                    session["total"] = None
                    unit, unit_plural = get_unit_info(new_product)
                    reply = get_template(lang, "product_found").format(
                        product_name=new_product["Product_Name"],
                        price=new_product.get("Base_Price", ""),
                        unit=unit,
                        unit_plural=unit_plural
                    )
                    logger.info(f"🔄 Product switched to: {new_product['Product_Name']}")
                elif new_candidates:
                    options = "\n".join([f"  {i+1}. {p['Product_Name']}" for i, p in enumerate(new_candidates)])
                    reply = get_template(lang, "disambiguation").format(options=options)
                else:
                    # Try parsing as quantity anyway
                    qty = extract_quantity(text, unit_type)
                    if qty is not None and qty > 0:
                        price = float(product.get("Base_Price", 0))
                        total = round(price * qty, 2)
                        
                        session["quantity"] = qty
                        session["total"] = total
                        session["state"] = "WAITING_CONFIRMATION"
                        
                        # Update quantity in LEADS_ACTIVE
                        if session.get("lead_id"):
                            sheets.update_active_lead_quantity(session["lead_id"], qty, total)
                        
                        qty_display = format_quantity_with_unit(qty, unit_type)
                        reply = get_template(lang, "quantity_confirm").format(
                            quantity=qty_display.split()[0],
                            unit=qty_display.split()[-1] if len(qty_display.split()) > 1 else unit,
                            total=total
                        )
                        logger.info(f"✅ Quantity={qty}, Total=₹{total}, state → WAITING_CONFIRMATION")
                    else:
                        reply = get_template(lang, "already_waiting_qty").format(
                            product_name=product["Product_Name"],
                            price=product.get("Base_Price", ""),
                            unit=unit,
                            unit_plural=unit_plural
                        )
            else:
                # First, try to resolve as a product name (user may want to switch products)
                new_product, new_candidates = resolve_product(text, products)
                
                if new_product and new_product.get("Product_Name") != product.get("Product_Name"):
                    # User switched to a different product
                    session["product"] = new_product
                    session["quantity"] = None
                    session["total"] = None
                    unit, unit_plural = get_unit_info(new_product)
                    
                    # Update ACTIVE lead with new product
                    if session.get("lead_id"):
                        sheets.cancel_active_lead(session["lead_id"])
                    lead_id = sheets.create_active_lead(phone, new_product)
                    session["lead_id"] = lead_id
                    
                    reply = get_template(lang, "product_found").format(
                        product_name=new_product["Product_Name"],
                        price=new_product.get("Base_Price", ""),
                        unit=unit,
                        unit_plural=unit_plural
                    )
                    logger.info(f"🔄 Product switched to: {new_product['Product_Name']}")
                elif new_candidates:
                    # Multiple matches — ask clarification
                    options = "\n".join([f"  {i+1}. {p['Product_Name']}" for i, p in enumerate(new_candidates)])
                    reply = get_template(lang, "disambiguation").format(options=options)
                    logger.info(f"🔢 Disambiguation: {len(new_candidates)} candidates shown")
                else:
                    # No product match — try to extract quantity
                    qty = extract_quantity(text, unit_type)
                    
                    if qty is not None and qty > 0:
                        price = float(product.get("Base_Price", 0))
                        total = round(price * qty, 2)
                        
                        session["quantity"] = qty
                        session["total"] = total
                        session["state"] = "WAITING_CONFIRMATION"
                        
                        # Update quantity in LEADS_ACTIVE
                        if session.get("lead_id"):
                            sheets.update_active_lead_quantity(session["lead_id"], qty, total)
                        
                        qty_display = format_quantity_with_unit(qty, unit_type)
                        reply = get_template(lang, "quantity_confirm").format(
                            quantity=qty_display.split()[0],
                            unit=qty_display.split()[-1] if len(qty_display.split()) > 1 else unit,
                            total=total
                        )
                        logger.info(f"✅ Quantity={qty}, Total=₹{total}, state → WAITING_CONFIRMATION")
                    else:
                        reply = get_template(lang, "invalid_quantity")
        
        # ----- STATE: WAITING_CONFIRMATION -----
        elif state == "WAITING_CONFIRMATION":
            product = session["product"]
            quantity = session["quantity"]
            total = session["total"]
            
            if is_confirmation(text, ai_intent):
                # ✅ CREATE LEAD NOW (only at confirmation!)
                success = sheets.create_confirmed_lead(phone, product, quantity, total)
                
                if success:
                    # Notify owner via Telegram
                    notification_data = {
                        "Customer_Name": "WhatsApp Customer",
                        "Phone": phone,
                        "Product_Name": product.get("Product_Name", ""),
                        "Quantity_Asked": str(quantity),
                        "Price_Shown": str(product.get("Base_Price", "")),
                        "Status": "CONFIRMED"
                    }
                    notify_owner(notification_data)
                    
                    reply = get_template(lang, "order_confirmed")
                    logger.info(f"✅ ORDER CONFIRMED: {product.get('Product_Name')} x{quantity} = ₹{total}")
                else:
                    reply = "Sorry sir, there was an error processing the order. Please try again."
                
                # Clear session for next order
                clear_session(phone)
            
            elif is_hard_cancel(text):
                # Update ACTIVE lead to CANCELLED in LEADS_ACTIVE
                if session.get("lead_id"):
                    sheets.cancel_active_lead(session["lead_id"])
                clear_session(phone)
                reply = get_template(lang, "order_cancelled")
                logger.info(f"❌ Order cancelled by customer")
            
            elif is_soft_cancel(text, ai_intent):
                qty_info = f", Quantity: {quantity}" if quantity else ""
                unit, unit_plural = get_unit_info(product)
                reply = get_template(lang, "cancel_confirm").format(
                    product_name=product.get("Product_Name", ""),
                    quantity_line=qty_info,
                    unit=unit
                )
                logger.info(f"⚠️ Soft cancel detected in WAITING_CONFIRMATION, asking for confirmation")
            
            else:
                # User might want to change quantity
                unit_type = product.get("Unit_Type", "PIECE").upper()
                new_qty = extract_quantity(text, unit_type)
                
                if new_qty is not None and new_qty > 0:
                    price = float(product.get("Base_Price", 0))
                    new_total = round(price * new_qty, 2)
                    
                    session["quantity"] = new_qty
                    session["total"] = new_total
                    
                    # Update quantity in LEADS_ACTIVE
                    if session.get("lead_id"):
                        sheets.update_active_lead_quantity(session["lead_id"], new_qty, new_total)
                    
                    unit, unit_plural = get_unit_info(product)
                    qty_display = format_quantity_with_unit(new_qty, unit_type)
                    reply = get_template(lang, "quantity_confirm").format(
                        quantity=qty_display.split()[0],
                        unit=qty_display.split()[-1] if len(qty_display.split()) > 1 else unit,
                        total=new_total
                    )
                    logger.info(f"🔄 Quantity updated to {new_qty}, Total=₹{new_total}")
                else:
                    # Re-show confirmation
                    unit, unit_plural = get_unit_info(product)
                    qty_display = format_quantity_with_unit(quantity, unit_type)
                    reply = get_template(lang, "quantity_confirm").format(
                        quantity=qty_display.split()[0],
                        unit=qty_display.split()[-1] if len(qty_display.split()) > 1 else unit,
                        total=total
                    )
        
        # ========== SEND REPLY ==========
        if reply:
            send_whatsapp_message(phone, reply)
        
        return "EVENT_RECEIVED", 200
    
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}", exc_info=True)
        return "EVENT_RECEIVED", 200


@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Front Office Manager v2",
        "products_loaded": len(sheets.get_products()),
        "keywords_indexed": len(sheets.get_keyword_map()),
        "active_sessions": len(session_store)
    }, 200


# ==================== MAIN ====================

if __name__ == "__main__":
    logger.info(f"🌐 Starting Flask server on port {Config.FLASK_PORT}")
    app.run(host='0.0.0.0', port=Config.FLASK_PORT, debug=Config.DEBUG_MODE, threaded=True)
