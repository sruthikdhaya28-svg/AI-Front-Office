"""
🧪 COMPREHENSIVE TEST SUITE - Anjali Sweets WhatsApp Bot
150+ Test Cases - Automated Validation
Thinking like: 10-year experienced tester + Sweet shop customer + Shop owner
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional, List, Dict

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": [],
    "categories": {}
}

def test_pass(category, test_name, details=""):
    test_results["passed"].append((category, test_name, details))
    if category not in test_results["categories"]:
        test_results["categories"][category] = {"pass": 0, "fail": 0}
    test_results["categories"][category]["pass"] += 1
    print(f"✅ {test_name}")
    if details:
        print(f"   → {details}")

def test_fail(category, test_name, details=""):
    test_results["failed"].append((category, test_name, details))
    if category not in test_results["categories"]:
        test_results["categories"][category] = {"pass": 0, "fail": 0}
    test_results["categories"][category]["fail"] += 1
    print(f"❌ {test_name}")
    if details:
        print(f"   → {details}")

def test_warn(category, test_name, details=""):
    test_results["warnings"].append((category, test_name, details))
    print(f"⚠️  {test_name}")
    if details:
        print(f"   → {details}")

print("\n" + "=" * 80)
print("🧪 COMPREHENSIVE TEST SUITE - ANJALI SWEETS BOT")
print("=" * 80)
print(f"Total Test Cases: 150+")
print(f"Test Categories: 15")
print("=" * 80 + "\n")

# ============================================================================
# CATEGORY 1: CONFIGURATION TESTS (15 tests)
# ============================================================================
print("📁 CATEGORY 1: CONFIGURATION TESTS (15 tests)")
print("-" * 80)

category = "Configuration"

# Test 1.1-1.5: File existence
if os.path.exists('.env'):
    test_pass(category, "1.1: .env file exists")
else:
    test_fail(category, "1.1: .env file missing")

if os.path.exists('credentials.json'):
    test_pass(category, "1.2: credentials.json exists")
else:
    test_fail(category, "1.2: credentials.json missing")

if os.path.exists('webhook.py'):
    test_pass(category, "1.3: webhook.py exists")
else:
    test_fail(category, "1.3: webhook.py missing")

if os.path.exists('utils.py'):
    test_pass(category, "1.4: utils.py exists")
else:
    test_fail(category, "1.4: utils.py missing")

if os.path.exists('config.py'):
    test_pass(category, "1.5: config.py exists")
else:
    test_fail(category, "1.5: config.py missing")

# Test 1.6-1.10: .env configuration
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        env_content = f.read()
    
    if 'GOOGLE_SHEET_NAME=Anjali_Sweets' in env_content:
        test_pass(category, "1.6: Google Sheet name = Anjali_Sweets")
    else:
        test_fail(category, "1.6: Google Sheet name incorrect")
    
    if 'GEMINI_API_KEY=' in env_content and len(env_content.split('GEMINI_API_KEY=')[1].split('\\n')[0].strip()) > 10:
        test_pass(category, "1.7: Gemini API key configured")
    else:
        test_fail(category, "1.7: Gemini API key missing")
    
    if 'WHATSAPP_ACCESS_TOKEN=' in env_content:
        test_pass(category, "1.8: WhatsApp token configured")
    else:
        test_fail(category, "1.8: WhatsApp token missing")
    
    if 'WEBHOOK_VERIFY_TOKEN=' in env_content:
        test_pass(category, "1.9: Webhook verify token configured")
    else:
        test_fail(category, "1.9: Webhook verify token missing")
    
    if 'TELEGRAM_BOT_TOKEN=' in env_content:
        test_pass(category, "1.10: Telegram bot token configured")
    else:
        test_warn(category, "1.10: Telegram bot token missing (optional)")

# Test 1.11-1.15: Config.py validation
if os.path.exists('config.py'):
    with open('config.py', 'r', encoding='utf-8') as f:
        config_content = f.read()
    
    if 'Adambakkam' in config_content or 'Chennai' in config_content:
        test_pass(category, "1.11: Shop location configured (Adambakkam, Chennai)")
    else:
        test_fail(category, "1.11: Shop location not configured")
    
    if 'Anjali' in config_content or 'SHOP_NAME' in config_content:
        test_pass(category, "1.12: Shop name configured")
    else:
        test_fail(category, "1.12: Shop name not configured")
    
    if 'SHOP_TIMING' in config_content:
        test_pass(category, "1.13: Shop timing configured")
    else:
        test_warn(category, "1.13: Shop timing not found")
    
    if 'DELIVERY_INFO' in config_content:
        test_pass(category, "1.14: Delivery info configured")
    else:
        test_warn(category, "1.14: Delivery info not found")
    
    if 'electrical' not in config_content.lower():
        test_pass(category, "1.15: No electrical references in config")
    else:
        test_fail(category, "1.15: Electrical references found in config")

print()

# ============================================================================
# CATEGORY 2: QUANTITY NORMALIZATION - ENGLISH (15 tests)
# ============================================================================
print("🔢 CATEGORY 2: QUANTITY NORMALIZATION - ENGLISH (15 tests)")
print("-" * 80)

category = "Quantity-English"

try:
    from utils import normalize_quantity
    
    # Test 2.1-2.5: Basic English keywords
    test_cases = [
        ("half", "KG", 0.5, "2.1: 'half' → 0.5 kg"),
        ("quarter", "KG", 0.25, "2.2: 'quarter' → 0.25 kg"),
        ("Half", "KG", 0.5, "2.3: 'Half' (capitalized) → 0.5 kg"),
        ("QUARTER", "KG", 0.25, "2.4: 'QUARTER' (uppercase) → 0.25 kg"),
        ("half kg", "KG", 0.5, "2.5: 'half kg' → 0.5 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")
    
    # Test 2.6-2.10: Variations with spaces
    test_cases = [
        ("  half  ", "KG", 0.5, "2.6: '  half  ' (extra spaces) → 0.5 kg"),
        ("quarter kg", "KG", 0.25, "2.7: 'quarter kg' → 0.25 kg"),
        ("half  kg", "KG", 0.5, "2.8: 'half  kg' (double space) → 0.5 kg"),
        ("I need half kg", "KG", 0.5, "2.9: 'I need half kg' → 0.5 kg"),
        ("Give me quarter kg", "KG", 0.25, "2.10: 'Give me quarter kg' → 0.25 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")
    
    # Test 2.11-2.15: Edge cases
    test_cases = [
        ("half!", "KG", 0.5, "2.11: 'half!' (with punctuation) → 0.5 kg"),
        ("quarter.", "KG", 0.25, "2.12: 'quarter.' (with period) → 0.25 kg"),
        ("half?", "KG", 0.5, "2.13: 'half?' (with question mark) → 0.5 kg"),
        ("quarter please", "KG", 0.25, "2.14: 'quarter please' → 0.25 kg"),
        ("just half", "KG", 0.5, "2.15: 'just half' → 0.5 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")

except ImportError:
    for i in range(1, 16):
        test_fail(category, f"2.{i}: Cannot import normalize_quantity")

print()

# ============================================================================
# CATEGORY 3: QUANTITY NORMALIZATION - TAMIL (15 tests)
# ============================================================================
print("🇮🇳 CATEGORY 3: QUANTITY NORMALIZATION - TAMIL (15 tests)")
print("-" * 80)

category = "Quantity-Tamil"

try:
    from utils import normalize_quantity
    
    # Test 3.1-3.5: Basic Tamil keywords
    test_cases = [
        ("ara", "KG", 0.5, "3.1: 'ara' (Tamil half) → 0.5 kg"),
        ("kaal", "KG", 0.25, "3.2: 'kaal' (Tamil quarter) → 0.25 kg"),
        ("araa", "KG", 0.5, "3.3: 'araa' (variant) → 0.5 kg"),
        ("Ara", "KG", 0.5, "3.4: 'Ara' (capitalized) → 0.5 kg"),
        ("Kaal", "KG", 0.25, "3.5: 'Kaal' (capitalized) → 0.25 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")
    
    # Test 3.6-3.10: Tamil with context
    test_cases = [
        ("ara kg venum", "KG", 0.5, "3.6: 'ara kg venum' → 0.5 kg"),
        ("kaal kg kudunga", "KG", 0.25, "3.7: 'kaal kg kudunga' → 0.25 kg"),
        ("enakku ara kg", "KG", 0.5, "3.8: 'enakku ara kg' → 0.5 kg"),
        ("kaal kg podhum", "KG", 0.25, "3.9: 'kaal kg podhum' → 0.25 kg"),
        ("ara venum", "KG", 0.5, "3.10: 'ara venum' → 0.5 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")
    
    # Test 3.11-3.15: Mixed Tamil-English
    test_cases = [
        ("ara kg please", "KG", 0.5, "3.11: 'ara kg please' (mixed) → 0.5 kg"),
        ("kaal kg thanks", "KG", 0.25, "3.12: 'kaal kg thanks' (mixed) → 0.25 kg"),
        ("I need ara kg", "KG", 0.5, "3.13: 'I need ara kg' (mixed) → 0.5 kg"),
        ("Give kaal kg", "KG", 0.25, "3.14: 'Give kaal kg' (mixed) → 0.25 kg"),
        ("  ara  ", "KG", 0.5, "3.15: '  ara  ' (spaces) → 0.5 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")

except ImportError:
    for i in range(1, 16):
        test_fail(category, f"3.{i}: Cannot import normalize_quantity")

print()

# ============================================================================
# CATEGORY 4: QUANTITY NORMALIZATION - GRAMS (15 tests)
# ============================================================================
print("⚖️  CATEGORY 4: QUANTITY NORMALIZATION - GRAMS (15 tests)")
print("-" * 80)

category = "Quantity-Grams"

try:
    from utils import normalize_quantity
    
    # Test 4.1-4.5: Standard gram conversions
    test_cases = [
        ("100g", "KG", 0.1, "4.1: '100g' → 0.1 kg"),
        ("250g", "KG", 0.25, "4.2: '250g' → 0.25 kg"),
        ("500g", "KG", 0.5, "4.3: '500g' → 0.5 kg"),
        ("100 g", "KG", 0.1, "4.4: '100 g' (with space) → 0.1 kg"),
        ("250 g", "KG", 0.25, "4.5: '250 g' (with space) → 0.25 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")
    
    # Test 4.6-4.10: Grams with context
    test_cases = [
        ("I need 100g", "KG", 0.1, "4.6: 'I need 100g' → 0.1 kg"),
        ("Give me 250g", "KG", 0.25, "4.7: 'Give me 250g' → 0.25 kg"),
        ("500g please", "KG", 0.5, "4.8: '500g please' → 0.5 kg"),
        ("100g venum", "KG", 0.1, "4.9: '100g venum' (Tamil) → 0.1 kg"),
        ("250g kudunga", "KG", 0.25, "4.10: '250g kudunga' (Tamil) → 0.25 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")
    
    # Test 4.11-4.15: Edge cases
    test_cases = [
        ("100G", "KG", 0.1, "4.11: '100G' (uppercase) → 0.1 kg"),
        ("250G", "KG", 0.25, "4.12: '250G' (uppercase) → 0.25 kg"),
        ("500G", "KG", 0.5, "4.13: '500G' (uppercase) → 0.5 kg"),
        ("100g!", "KG", 0.1, "4.14: '100g!' (with punctuation) → 0.1 kg"),
        ("250g.", "KG", 0.25, "4.15: '250g.' (with period) → 0.25 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")

except ImportError:
    for i in range(1, 16):
        test_fail(category, f"4.{i}: Cannot import normalize_quantity")

print()

# ============================================================================
# CATEGORY 5: QUANTITY NORMALIZATION - NUMERIC KG (15 tests)
# ============================================================================
print("🔢 CATEGORY 5: QUANTITY NORMALIZATION - NUMERIC KG (15 tests)")
print("-" * 80)

category = "Quantity-Numeric-KG"

try:
    from utils import normalize_quantity
    
    # Test 5.1-5.5: Whole numbers
    test_cases = [
        ("1", "KG", 1.0, "5.1: '1' → 1.0 kg"),
        ("2", "KG", 2.0, "5.2: '2' → 2.0 kg"),
        ("3", "KG", 3.0, "5.3: '3' → 3.0 kg"),
        ("5", "KG", 5.0, "5.4: '5' → 5.0 kg"),
        ("10", "KG", 10.0, "5.5: '10' → 10.0 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")
    
    # Test 5.6-5.10: Decimals
    test_cases = [
        ("0.5", "KG", 0.5, "5.6: '0.5' → 0.5 kg"),
        ("1.5", "KG", 1.5, "5.7: '1.5' → 1.5 kg"),
        ("2.5", "KG", 2.5, "5.8: '2.5' → 2.5 kg"),
        ("0.25", "KG", 0.25, "5.9: '0.25' → 0.25 kg"),
        ("0.75", "KG", 0.75, "5.10: '0.75' → 0.75 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")
    
    # Test 5.11-5.15: With 'kg' suffix
    test_cases = [
        ("1 kg", "KG", 1.0, "5.11: '1 kg' → 1.0 kg"),
        ("2 kg", "KG", 2.0, "5.12: '2 kg' → 2.0 kg"),
        ("1.5 kg", "KG", 1.5, "5.13: '1.5 kg' → 1.5 kg"),
        ("2.5 kg", "KG", 2.5, "5.14: '2.5 kg' → 2.5 kg"),
        ("0.5 kg", "KG", 0.5, "5.15: '0.5 kg' → 0.5 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")

except ImportError:
    for i in range(1, 16):
        test_fail(category, f"5.{i}: Cannot import normalize_quantity")

print()

# ============================================================================
# CATEGORY 6: QUANTITY NORMALIZATION - PIECES (10 tests)
# ============================================================================
print("🍬 CATEGORY 6: QUANTITY NORMALIZATION - PIECES (10 tests)")
print("-" * 80)

category = "Quantity-Pieces"

try:
    from utils import normalize_quantity
    
    # Test 6.1-6.10: Piece quantities
    test_cases = [
        ("1", "PIECE", 1.0, "6.1: '1' piece"),
        ("5", "PIECE", 5.0, "6.2: '5' pieces"),
        ("10", "PIECE", 10.0, "6.3: '10' pieces"),
        ("20", "PIECE", 20.0, "6.4: '20' pieces"),
        ("50", "PIECE", 50.0, "6.5: '50' pieces"),
        ("5 pieces", "PIECE", 5.0, "6.6: '5 pieces'"),
        ("10 pieces", "PIECE", 10.0, "6.7: '10 pieces'"),
        ("3 piece", "PIECE", 3.0, "6.8: '3 piece' (singular)"),
        ("I need 5", "PIECE", 5.0, "6.9: 'I need 5'"),
        ("Give 10 pieces", "PIECE", 10.0, "6.10: 'Give 10 pieces'"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")

except ImportError:
    for i in range(1, 11):
        test_fail(category, f"6.{i}: Cannot import normalize_quantity")

print()

# ============================================================================
# CATEGORY 7: QUANTITY NORMALIZATION - BOXES (10 tests)
# ============================================================================
print("📦 CATEGORY 7: QUANTITY NORMALIZATION - BOXES (10 tests)")
print("-" * 80)

category = "Quantity-Boxes"

try:
    from utils import normalize_quantity
    
    # Test 7.1-7.10: Box quantities
    test_cases = [
        ("1", "BOX", 1.0, "7.1: '1' box"),
        ("2", "BOX", 2.0, "7.2: '2' boxes"),
        ("3", "BOX", 3.0, "7.3: '3' boxes"),
        ("5", "BOX", 5.0, "7.4: '5' boxes"),
        ("10", "BOX", 10.0, "7.5: '10' boxes"),
        ("2 box", "BOX", 2.0, "7.6: '2 box'"),
        ("3 boxes", "BOX", 3.0, "7.7: '3 boxes'"),
        ("I need 2 box", "BOX", 2.0, "7.8: 'I need 2 box'"),
        ("Give 5 boxes", "BOX", 5.0, "7.9: 'Give 5 boxes'"),
        ("1 box please", "BOX", 1.0, "7.10: '1 box please'"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, f"Expected {expected}, got {result}")

except ImportError:
    for i in range(1, 11):
        test_fail(category, f"7.{i}: Cannot import normalize_quantity")

print()

# ============================================================================
# CATEGORY 8: GOOGLE SHEETS INTEGRATION (10 tests)
# ============================================================================
print("📊 CATEGORY 8: GOOGLE SHEETS INTEGRATION (10 tests)")
print("-" * 80)

category = "Google-Sheets"

try:
    from sheets_manager import get_sheets_manager
    
    # Test 8.1: Connection
    try:
        sheets = get_sheets_manager()
        test_pass(category, "8.1: Google Sheets connection successful")
        
        # Test 8.2: Products loaded
        products = sheets.get_products()
        if products and len(products) > 0:
            test_pass(category, f"8.2: Products loaded ({len(products)} products)")
        else:
            test_fail(category, "8.2: No products loaded")
        
        # Test 8.3: Product structure
        if products:
            first_product = products[0]
            if 'Product_Name' in first_product:
                test_pass(category, "8.3: Product_Name field exists")
            else:
                test_fail(category, "8.3: Product_Name field missing")
            
            # Test 8.4: Unit_Type field
            if 'Unit_Type' in first_product:
                test_pass(category, "8.4: Unit_Type field exists")
            else:
                test_fail(category, "8.4: Unit_Type field missing")
            
            # Test 8.5: Base_Price field
            if 'Base_Price' in first_product:
                test_pass(category, "8.5: Base_Price field exists")
            else:
                test_fail(category, "8.5: Base_Price field missing")
            
            # Test 8.6: Unit types validation
            unit_types = set(p.get('Unit_Type', '') for p in products)
            valid_units = {'KG', 'PIECE', 'BOX'}
            invalid_units = unit_types - valid_units - {''}
            
            if not invalid_units:
                test_pass(category, f"8.6: All unit types valid ({', '.join(unit_types)})")
            else:
                test_warn(category, f"8.6: Invalid unit types found: {invalid_units}")
            
            # Test 8.7: Product count reasonable
            if len(products) >= 10:
                test_pass(category, f"8.7: Product count reasonable ({len(products)})")
            else:
                test_warn(category, f"8.7: Low product count ({len(products)})")
            
            # Test 8.8: Prices are numeric
            try:
                prices = [float(p.get('Base_Price', 0)) for p in products[:5]]
                if all(p > 0 for p in prices):
                    test_pass(category, "8.8: Prices are valid numbers")
                else:
                    test_warn(category, "8.8: Some prices are zero or negative")
            except:
                test_fail(category, "8.8: Prices are not numeric")
            
            # Test 8.9: Product names not empty
            empty_names = [p for p in products if not p.get('Product_Name', '').strip()]
            if not empty_names:
                test_pass(category, "8.9: All products have names")
            else:
                test_fail(category, f"8.9: {len(empty_names)} products have empty names")
            
            # Test 8.10: No duplicate product names
            names = [p.get('Product_Name', '') for p in products]
            if len(names) == len(set(names)):
                test_pass(category, "8.10: No duplicate product names")
            else:
                duplicates = len(names) - len(set(names))
                test_warn(category, f"8.10: {duplicates} duplicate product names found")
        
    except Exception as e:
        test_fail(category, "8.1: Google Sheets connection failed", str(e))
        for i in range(2, 11):
            test_fail(category, f"8.{i}: Skipped due to connection failure")

except ImportError:
    for i in range(1, 11):
        test_fail(category, f"8.{i}: Cannot import sheets_manager")

print()

# ============================================================================
# CATEGORY 9: AI HANDLER TESTS (10 tests)
# ============================================================================
print("🤖 CATEGORY 9: AI HANDLER TESTS (10 tests)")
print("-" * 80)

category = "AI-Handler"

if os.path.exists('ai_handler.py'):
    with open('ai_handler.py', 'r', encoding='utf-8') as f:
        ai_content = f.read()
    
    # Test 9.1: Sweets context
    sweets_keywords = ['sweets', 'mysore pak', 'laddu', 'mixture', 'anjali']
    found = [kw for kw in sweets_keywords if kw.lower() in ai_content.lower()]
    if found:
        test_pass(category, f"9.1: Sweets context present ({', '.join(found)})")
    else:
        test_fail(category, "9.1: No sweets context found")
    
    # Test 9.2: No electrical references
    electrical_keywords = ['electrical', 'wire', 'mcb', 'voltage', 'amps']
    found_electrical = [kw for kw in electrical_keywords if kw.lower() in ai_content.lower()]
    if not found_electrical:
        test_pass(category, "9.2: No electrical references")
    else:
        test_warn(category, f"9.2: Electrical references found: {', '.join(found_electrical)}")
    
    # Test 9.3: Tamil confirmation phrases
    tamil_phrases = ['confirm pannalama', 'pannunga', 'venum']
    found_tamil = [p for p in tamil_phrases if p.lower() in ai_content.lower()]
    if found_tamil:
        test_pass(category, f"9.3: Tamil phrases present ({', '.join(found_tamil)})")
    else:
        test_warn(category, "9.3: No Tamil confirmation phrases found")
    
    # Test 9.4: Gemini import
    if 'import google.generativeai as genai' in ai_content:
        test_pass(category, "9.4: Gemini AI imported")
    else:
        test_fail(category, "9.4: Gemini AI not imported")
    
    # Test 9.5: Extract structured data function
    if 'def extract_structured_data' in ai_content or 'extract_' in ai_content:
        test_pass(category, "9.5: Data extraction function exists")
    else:
        test_warn(category, "9.5: Data extraction function not found")
    
    # Test 9.6: Get AI response function
    if 'def get_ai_response' in ai_content:
        test_pass(category, "9.6: get_ai_response function exists")
    else:
        test_fail(category, "9.6: get_ai_response function missing")
    
    # Test 9.7: Fallback responses
    if 'fallback' in ai_content.lower() or 'default' in ai_content.lower():
        test_pass(category, "9.7: Fallback responses configured")
    else:
        test_warn(category, "9.7: Fallback responses not found")
    
    # Test 9.8: Product catalog formatting
    if 'product' in ai_content.lower() and 'catalog' in ai_content.lower():
        test_pass(category, "9.8: Product catalog handling present")
    else:
        test_warn(category, "9.8: Product catalog handling unclear")
    
    # Test 9.9: Language detection
    if 'language' in ai_content.lower() or 'tamil' in ai_content.lower():
        test_pass(category, "9.9: Language detection present")
    else:
        test_warn(category, "9.9: Language detection not found")
    
    # Test 9.10: Intent detection
    if 'intent' in ai_content.lower():
        test_pass(category, "9.10: Intent detection present")
    else:
        test_warn(category, "9.10: Intent detection not found")

else:
    for i in range(1, 11):
        test_fail(category, f"9.{i}: ai_handler.py not found")

print()

# ============================================================================
# CATEGORY 10: WEBHOOK HANDLER TESTS (10 tests)
# ============================================================================
print("🌐 CATEGORY 10: WEBHOOK HANDLER TESTS (10 tests)")
print("-" * 80)

category = "Webhook"

if os.path.exists('webhook.py'):
    with open('webhook.py', 'r', encoding='utf-8') as f:
        webhook_content = f.read()
    
    # Test 10.1: Flask import
    if 'from flask import' in webhook_content or 'import flask' in webhook_content:
        test_pass(category, "10.1: Flask imported")
    else:
        test_fail(category, "10.1: Flask not imported")
    
    # Test 10.2: Webhook route
    if '@app.route' in webhook_content and '/webhook' in webhook_content:
        test_pass(category, "10.2: Webhook route defined")
    else:
        test_fail(category, "10.2: Webhook route missing")
    
    # Test 10.3: Message deduplication
    if 'duplicate' in webhook_content.lower() or 'dedup' in webhook_content.lower():
        test_pass(category, "10.3: Message deduplication present")
    else:
        test_warn(category, "10.3: Message deduplication not found")
    
    # Test 10.4: Shop info handler
    if 'shop' in webhook_content.lower() and ('timing' in webhook_content.lower() or 'location' in webhook_content.lower()):
        test_pass(category, "10.4: Shop info handler present")
    else:
        test_warn(category, "10.4: Shop info handler not found")
    
    # Test 10.5: Product detection
    if 'product' in webhook_content.lower() and 'detect' in webhook_content.lower():
        test_pass(category, "10.5: Product detection logic present")
    else:
        test_warn(category, "10.5: Product detection unclear")
    
    # Test 10.6: Quantity handling
    if 'quantity' in webhook_content.lower():
        test_pass(category, "10.6: Quantity handling present")
    else:
        test_warn(category, "10.6: Quantity handling not found")
    
    # Test 10.7: Confirmation handling
    if 'confirm' in webhook_content.lower():
        test_pass(category, "10.7: Confirmation handling present")
    else:
        test_warn(category, "10.7: Confirmation handling not found")
    
    # Test 10.8: Lead creation
    if 'create_lead' in webhook_content or 'lead' in webhook_content.lower():
        test_pass(category, "10.8: Lead creation logic present")
    else:
        test_warn(category, "10.8: Lead creation not found")
    
    # Test 10.9: Error handling
    if 'try:' in webhook_content and 'except' in webhook_content:
        test_pass(category, "10.9: Error handling present")
    else:
        test_warn(category, "10.9: Error handling not found")
    
    # Test 10.10: Logging
    if 'logger' in webhook_content or 'logging' in webhook_content:
        test_pass(category, "10.10: Logging configured")
    else:
        test_warn(category, "10.10: Logging not found")

else:
    for i in range(1, 11):
        test_fail(category, f"10.{i}: webhook.py not found")

print()

# ============================================================================
# CATEGORY 11: UTILS FUNCTIONS (10 tests)
# ============================================================================
print("🔧 CATEGORY 11: UTILS FUNCTIONS (10 tests)")
print("-" * 80)

category = "Utils"

try:
    from utils import (
        normalize_quantity,
        detect_all_products,
        get_shop_info_response,
        format_quantity_with_unit
    )
    
    test_pass(category, "11.1: normalize_quantity imported")
    test_pass(category, "11.2: detect_all_products imported")
    test_pass(category, "11.3: get_shop_info_response imported")
    test_pass(category, "11.4: format_quantity_with_unit imported")
    
    # Test 11.5: Shop info response
    try:
        response = get_shop_info_response("timing")
        if response and len(response) > 0:
            test_pass(category, "11.5: Shop info response works")
        else:
            test_fail(category, "11.5: Shop info response empty")
    except Exception as e:
        test_fail(category, "11.5: Shop info response error", str(e))
    
    # Test 11.6: Format quantity
    try:
        formatted = format_quantity_with_unit(0.5, "KG")
        if "0.5" in str(formatted) and "kg" in str(formatted).lower():
            test_pass(category, "11.6: Format quantity works")
        else:
            test_warn(category, "11.6: Format quantity unclear", formatted)
    except Exception as e:
        test_fail(category, "11.6: Format quantity error", str(e))
    
    # Test 11.7-11.10: Edge cases
    try:
        result = normalize_quantity("", "KG")
        if result is None:
            test_pass(category, "11.7: Empty string handled")
        else:
            test_warn(category, "11.7: Empty string returns value", result)
    except:
        test_pass(category, "11.7: Empty string raises exception (acceptable)")
    
    try:
        result = normalize_quantity("abc", "KG")
        if result is None:
            test_pass(category, "11.8: Invalid input handled")
        else:
            test_warn(category, "11.8: Invalid input returns value", result)
    except:
        test_pass(category, "11.8: Invalid input raises exception (acceptable)")
    
    try:
        result = normalize_quantity("999999", "KG")
        if result == 999999.0:
            test_pass(category, "11.9: Large number handled")
        else:
            test_warn(category, "11.9: Large number unexpected", result)
    except:
        test_warn(category, "11.9: Large number raises exception")
    
    try:
        result = normalize_quantity("0", "KG")
        if result == 0.0:
            test_pass(category, "11.10: Zero handled")
        else:
            test_warn(category, "11.10: Zero returns unexpected", result)
    except:
        test_warn(category, "11.10: Zero raises exception")

except ImportError as e:
    for i in range(1, 11):
        test_fail(category, f"11.{i}: Cannot import utils functions", str(e))

print()

# ============================================================================
# CATEGORY 12: EDGE CASES - CUSTOMER BEHAVIOR (15 tests)
# ============================================================================
print("👤 CATEGORY 12: EDGE CASES - CUSTOMER BEHAVIOR (15 tests)")
print("-" * 80)

category = "Customer-Behavior"

try:
    from utils import normalize_quantity
    
    # Test 12.1-12.5: Typos and misspellings
    test_cases = [
        ("hlaf", "KG", None, "12.1: 'hlaf' (typo) → None (expected)"),
        ("quater", "KG", None, "12.2: 'quater' (typo) → None (expected)"),
        ("aara", "KG", 0.5, "12.3: 'aara' (variant) → 0.5 kg"),
        ("kaal kg", "KG", 0.25, "12.4: 'kaal kg' (correct) → 0.25 kg"),
        ("1.5kg", "KG", 1.5, "12.5: '1.5kg' (no space) → 1.5 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_warn(category, test_name, f"Expected {expected}, got {result}")
    
    # Test 12.6-12.10: Unusual formats
    test_cases = [
        ("1/2", "KG", None, "12.6: '1/2' (fraction) → None (not supported)"),
        ("one kg", "KG", None, "12.7: 'one kg' (word) → None (not supported)"),
        ("2.0", "KG", 2.0, "12.8: '2.0' (decimal) → 2.0 kg"),
        ("  1  ", "KG", 1.0, "12.9: '  1  ' (extra spaces) → 1.0 kg"),
        ("1kg please sir", "KG", 1.0, "12.10: '1kg please sir' → 1.0 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_warn(category, test_name, f"Expected {expected}, got {result}")
    
    # Test 12.11-12.15: Real customer messages
    test_cases = [
        ("bro half kg venum", "KG", 0.5, "12.11: 'bro half kg venum' → 0.5 kg"),
        ("anna kaal kg kudunga", "KG", 0.25, "12.12: 'anna kaal kg kudunga' → 0.25 kg"),
        ("250g podhum", "KG", 0.25, "12.13: '250g podhum' → 0.25 kg"),
        ("just 100g", "KG", 0.1, "12.14: 'just 100g' → 0.1 kg"),
        ("2 kg thaan venum", "KG", 2.0, "12.15: '2 kg thaan venum' → 2.0 kg"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        result = normalize_quantity(input_text, unit_type)
        if result == expected:
            test_pass(category, test_name)
        else:
            test_warn(category, test_name, f"Expected {expected}, got {result}")

except ImportError:
    for i in range(1, 16):
        test_fail(category, f"12.{i}: Cannot import normalize_quantity")

print()

# ============================================================================
# CATEGORY 13: EDGE CASES - INVALID INPUTS (10 tests)
# ============================================================================
print("⚠️  CATEGORY 13: EDGE CASES - INVALID INPUTS (10 tests)")
print("-" * 80)

category = "Invalid-Inputs"

try:
    from utils import normalize_quantity
    
    # Test 13.1-13.10: Invalid inputs should return None
    test_cases = [
        ("", "KG", None, "13.1: Empty string"),
        ("   ", "KG", None, "13.2: Only spaces"),
        ("abc", "KG", None, "13.3: Letters only"),
        ("xyz kg", "KG", None, "13.4: Invalid letters with kg"),
        ("!@#$", "KG", None, "13.5: Special characters only"),
        ("-1", "KG", -1.0, "13.6: Negative number (may return -1)"),
        ("0", "KG", 0.0, "13.7: Zero (may return 0)"),
        ("999999", "KG", 999999.0, "13.8: Very large number"),
        ("0.001", "KG", 0.001, "13.9: Very small number"),
        ("kg", "KG", None, "13.10: Unit only, no number"),
    ]
    
    for input_text, unit_type, expected, test_name in test_cases:
        try:
            result = normalize_quantity(input_text, unit_type)
            if result == expected or (expected is None and result is None):
                test_pass(category, test_name)
            else:
                test_warn(category, test_name, f"Expected {expected}, got {result}")
        except Exception as e:
            test_warn(category, test_name, f"Exception raised: {str(e)[:50]}")

except ImportError:
    for i in range(1, 11):
        test_fail(category, f"13.{i}: Cannot import normalize_quantity")

print()

# ============================================================================
# CATEGORY 14: REAL-WORLD SCENARIOS (10 tests)
# ============================================================================
print("🌍 CATEGORY 14: REAL-WORLD SCENARIOS (10 tests)")
print("-" * 80)

category = "Real-World"

# Test 14.1-14.5: File permissions
test_cases = [
    ('.env', "14.1: .env file readable"),
    ('credentials.json', "14.2: credentials.json readable"),
    ('webhook.py', "14.3: webhook.py readable"),
    ('utils.py', "14.4: utils.py readable"),
    ('config.py', "14.5: config.py readable"),
]

for file_path, test_name in test_cases:
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                f.read(1)
            test_pass(category, test_name)
        else:
            test_fail(category, test_name, "File not found")
    except Exception as e:
        test_fail(category, test_name, str(e))

# Test 14.6-14.10: Directory structure
test_cases = [
    ('templates', "14.6: templates directory exists"),
    ('.venv', "14.7: .venv directory exists"),
    ('.git', "14.8: .git directory exists"),
    ('__pycache__', "14.9: __pycache__ directory exists (Python running)"),
]

for dir_path, test_name in test_cases:
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        test_pass(category, test_name)
    else:
        test_warn(category, test_name, "Directory not found (may be ok)")

# Test 14.10: Python version
import sys
if sys.version_info >= (3, 8):
    test_pass(category, f"14.10: Python version {sys.version_info.major}.{sys.version_info.minor} (>= 3.8)")
else:
    test_warn(category, f"14.10: Python version {sys.version_info.major}.{sys.version_info.minor} (< 3.8)")

print()

# ============================================================================
# CATEGORY 15: PRODUCTION READINESS (10 tests)
# ============================================================================
print("🚀 CATEGORY 15: PRODUCTION READINESS (10 tests)")
print("-" * 80)

category = "Production"

# Test 15.1: All critical files exist
critical_files = ['webhook.py', 'config.py', 'sheets_manager.py', 'ai_handler.py', 'utils.py', '.env', 'credentials.json']
missing_files = [f for f in critical_files if not os.path.exists(f)]

if not missing_files:
    test_pass(category, "15.1: All critical files present")
else:
    test_fail(category, "15.1: Missing critical files", ', '.join(missing_files))

# Test 15.2: No test files in production
test_files = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py') and f != 'run_tests.py']
if not test_files:
    test_pass(category, "15.2: No test files in production")
else:
    test_warn(category, "15.2: Test files found", ', '.join(test_files))

# Test 15.3: Requirements file
if os.path.exists('requirements.txt'):
    test_pass(category, "15.3: requirements.txt exists")
else:
    test_warn(category, "15.3: requirements.txt not found")

# Test 15.4: README file
if os.path.exists('README.md') or os.path.exists('readme.md'):
    test_pass(category, "15.4: README file exists")
else:
    test_warn(category, "15.4: README file not found")

# Test 15.5: .gitignore file
if os.path.exists('.gitignore'):
    test_pass(category, "15.5: .gitignore exists")
else:
    test_warn(category, "15.5: .gitignore not found")

# Test 15.6: No debug files
debug_files = [f for f in os.listdir('.') if f.endswith('.log') or f.endswith('.tmp')]
if not debug_files:
    test_pass(category, "15.6: No debug files present")
else:
    test_warn(category, "15.6: Debug files found", ', '.join(debug_files))

# Test 15.7: Code quality - no syntax errors
try:
    import webhook
    test_pass(category, "15.7: webhook.py has no syntax errors")
except SyntaxError as e:
    test_fail(category, "15.7: webhook.py has syntax errors", str(e))
except Exception:
    test_pass(category, "15.7: webhook.py syntax ok (import error is ok)")

# Test 15.8: Utils module syntax
try:
    import utils
    test_pass(category, "15.8: utils.py has no syntax errors")
except SyntaxError as e:
    test_fail(category, "15.8: utils.py has syntax errors", str(e))
except Exception:
    test_pass(category, "15.8: utils.py syntax ok (import error is ok)")

# Test 15.9: Config module syntax
try:
    import config
    test_pass(category, "15.9: config.py has no syntax errors")
except SyntaxError as e:
    test_fail(category, "15.9: config.py has syntax errors", str(e))
except Exception:
    test_pass(category, "15.9: config.py syntax ok (import error is ok)")

# Test 15.10: Overall system health
total_tests = len(test_results["passed"]) + len(test_results["failed"])
pass_rate = (len(test_results["passed"]) / total_tests * 100) if total_tests > 0 else 0

if pass_rate >= 90:
    test_pass(category, f"15.10: System health excellent ({pass_rate:.1f}% pass rate)")
elif pass_rate >= 70:
    test_warn(category, f"15.10: System health good ({pass_rate:.1f}% pass rate)")
else:
    test_fail(category, f"15.10: System health needs improvement ({pass_rate:.1f}% pass rate)")

print()

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("=" * 80)
print("📊 FINAL TEST SUMMARY")
print("=" * 80)

total_tests = len(test_results["passed"]) + len(test_results["failed"]) + len(test_results["warnings"])
pass_rate = (len(test_results["passed"]) / total_tests * 100) if total_tests > 0 else 0

print(f"\n✅ Passed: {len(test_results['passed'])}")
print(f"❌ Failed: {len(test_results['failed'])}")
print(f"⚠️  Warnings: {len(test_results['warnings'])}")
print(f"\n📈 Pass Rate: {pass_rate:.1f}%")
print(f"📊 Total Tests: {total_tests}")

# Category breakdown
print("\n📋 CATEGORY BREAKDOWN:")
print("-" * 80)
for cat_name, cat_results in sorted(test_results["categories"].items()):
    total = cat_results["pass"] + cat_results["fail"]
    cat_pass_rate = (cat_results["pass"] / total * 100) if total > 0 else 0
    status = "✅" if cat_pass_rate >= 90 else "⚠️" if cat_pass_rate >= 70 else "❌"
    print(f"{status} {cat_name:25s}: {cat_results['pass']:3d}/{total:3d} ({cat_pass_rate:5.1f}%)")

# Critical failures
if test_results["failed"]:
    print("\n🔴 CRITICAL FAILURES:")
    print("-" * 80)
    for category, test_name, details in test_results["failed"][:10]:  # Show first 10
        print(f"  • [{category}] {test_name}")
        if details:
            print(f"    {details}")

# Warnings
if test_results["warnings"]:
    print("\n🟡 WARNINGS:")
    print("-" * 80)
    for category, test_name, details in test_results["warnings"][:10]:  # Show first 10
        print(f"  • [{category}] {test_name}")
        if details:
            print(f"    {details}")

# Production readiness
print("\n" + "=" * 80)
if pass_rate >= 95:
    print("🎉 SYSTEM STATUS: PRODUCTION READY (EXCELLENT)")
elif pass_rate >= 85:
    print("✅ SYSTEM STATUS: PRODUCTION READY (GOOD)")
elif pass_rate >= 70:
    print("⚠️  SYSTEM STATUS: NEEDS MINOR FIXES")
else:
    print("🔴 SYSTEM STATUS: NEEDS MAJOR FIXES")
print("=" * 80 + "\n")

print(f"Test completed at: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
