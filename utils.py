"""
Utility functions for Anjali Sweets WhatsApp Bot
Handles quantity normalization, product detection, and shop information

v2 - Architecture Fix:
  - 3-level product resolution engine (exact → word-boundary → fuzzy)
  - Centralized extract_quantity() returning float always
"""
import re
from typing import Optional, List, Dict, Tuple
from config import Config
import logging
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

# ==================== CONSTANTS ====================

# Tamil/English word-to-number mappings for quantity extraction
WORD_QUANTITIES = {
    # English
    "half": 0.5,
    "quarter": 0.25,
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
    # Tamil transliteration
    "ara": 0.5,
    "kaal": 0.25,
    "onnu": 1.0,
    "rendu": 2.0,
    "moonu": 3.0,
    "naalu": 4.0,
    "ainthu": 5.0,
    "aaru": 6.0,
    "ezhu": 7.0,
    "ettu": 8.0,
    "onpathu": 9.0,
    "pathu": 10.0,
    # Tamil script
    "அர": 0.5,
    "கால்": 0.25,
}

# Gram-to-KG conversion patterns
GRAM_CONVERSIONS = {
    100: 0.1,
    150: 0.15,
    200: 0.2,
    250: 0.25,
    300: 0.3,
    500: 0.5,
    750: 0.75,
}

FUZZY_MATCH_THRESHOLD = 80  # Minimum similarity % for fuzzy matching

# Known aliases: culturally equivalent names that fuzzy matching can't catch
# Maps alias → canonical product name (as it appears in STOCK_MASTER)
PRODUCT_ALIASES = {
    # Jalebi vs Jangiri (South Indian name for jalebi)
    "jalebi": "Jangiri",
    "jelabi": "Jangiri",
    "jilebi": "Jangiri",
    "jilabi": "Jangiri",
    "imarti": "Jangiri",
    # Laddu variants
    "ladoo": "Laddu",
    "ladu": "Laddu",
    "laddoo": "Laddu",
    "laddo": "Laddu",
    # Mysore Pak variants
    "mysore pa": "Mysore Pak",
    "mysore pakk": "Mysore Pak",
    "mysorepak": "Mysore Pak",
    "mysoorpak": "Mysore Pak",
    "mysoor pak": "Mysore Pak",
    # Kaju Katli variants
    "kaju barfi": "Kaju Katli",
    "kaju burfi": "Kaju Katli",
    "cashew katli": "Kaju Katli",
    "cashew barfi": "Kaju Katli",
    # Cake variants
    "cke": "cake",
}



# ==================== QUANTITY EXTRACTION ====================

def parse_fraction(text: str) -> Optional[float]:
    """
    Parse fraction formats commonly used in Indian ordering
    
    Supports:
    - Simple fractions: "1/2", "3/4", "1/4"
    - Mixed numbers: "1 1/2", "2 3/4", "3 1/4"
    - With units: "1 1/2 kg", "3/4 kg"
    
    Args:
        text: User input text containing fraction
    
    Returns:
        Float value of the fraction, or None if no valid fraction found
    """
    text = text.strip().lower()
    
    # Pattern for mixed number: "1 1/2" or "2 3/4"
    mixed_pattern = r'(\d+)\s+(\d+)/(\d+)'
    mixed_match = re.search(mixed_pattern, text)
    
    if mixed_match:
        whole = int(mixed_match.group(1))
        numerator = int(mixed_match.group(2))
        denominator = int(mixed_match.group(3))
        
        if denominator == 0:
            return None
        
        fraction_value = numerator / denominator
        return whole + fraction_value
    
    # Pattern for simple fraction: "1/2" or "3/4"
    simple_pattern = r'(\d+)/(\d+)'
    simple_match = re.search(simple_pattern, text)
    
    if simple_match:
        numerator = int(simple_match.group(1))
        denominator = int(simple_match.group(2))
        
        if denominator == 0:
            return None
        
        return numerator / denominator
    
    return None


def extract_quantity(text: str, unit_type: str) -> Optional[float]:
    """
    Centralized quantity extraction - returns float ALWAYS.
    
    This is the SINGLE entry point for all quantity parsing.
    Call this BEFORE falling back to AI extraction.
    
    Priority order:
    1. Pure digit → int converted to float
    2. Gram patterns (100g, 250g, etc.) → convert to kg
    3. Fraction patterns (1/2, 1 1/2, etc.)
    4. Word quantities (half, ara, quarter, kaal, etc.)
    5. General decimal regex (``\\d+\\.?\\d*``)
    
    Args:
        text: User message text
        unit_type: Product unit type (KG, PIECE, BOX)
    
    Returns:
        Normalized quantity as float, or None if unparseable
    """
    if not text or not text.strip():
        return None
    
    text_clean = text.strip().lower()
    
    # ---- STEP 1: Pure digit ----
    if text_clean.isdigit():
        return float(text_clean)
    
    # ---- STEP 2: Gram conversions (KG items only) ----
    if unit_type == "KG":
        # Match patterns like "100g", "250 g", "500gm", "250 grams"
        gram_match = re.search(r'(\d+)\s*(?:g|gm|gms|gram|grams)\b', text_clean)
        if gram_match:
            grams = int(gram_match.group(1))
            if grams in GRAM_CONVERSIONS:
                result = GRAM_CONVERSIONS[grams]
                logger.info(f"📏 Gram conversion: {grams}g → {result} kg")
                return result
            else:
                # Generic gram to kg
                result = grams / 1000.0
                logger.info(f"📏 Gram conversion: {grams}g → {result} kg")
                return result
    
    # ---- STEP 3: Fraction patterns ----
    fraction_value = parse_fraction(text_clean)
    if fraction_value is not None:
        logger.info(f"📏 Fraction parsed: '{text}' → {fraction_value}")
        return fraction_value
    
    # ---- STEP 4: Word quantities ----
    for word, value in WORD_QUANTITIES.items():
        # Build word-boundary regex: \bword\b
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text_clean):
            logger.info(f"📏 Word quantity: '{word}' → {value}")
            return value
    
    # ---- STEP 5: General decimal/integer regex ----
    decimal_match = re.search(r'(\d+\.?\d*)', text_clean)
    if decimal_match:
        result = float(decimal_match.group(1))
        # For PIECE/BOX, always return int-like float
        if unit_type in ("PIECE", "BOX"):
            result = float(int(result))
        logger.info(f"📏 Numeric extraction: '{text}' → {result}")
        return result
    
    return None


# Keep old name as alias for backward compatibility with existing tests
normalize_quantity = extract_quantity


# ==================== NATURAL LANGUAGE CLEANUP ====================

# Phrases to strip from user messages before product matching.
# Order matters: longer phrases first to avoid partial matches.
CONVERSATIONAL_PREFIXES = [
    # English phrases
    "i need to order", "i want to order", "i would like to order",
    "i'd like to order", "i wanna order", "can i get",
    "can i order", "can i have", "could i get", "could i have",
    "i need some", "i want some", "give me some",
    "i need", "i want", "i wanna", "i wnat", "i require", "i'm looking for",
    "do you have any", "do you have", "do you sell",
    "is there any", "is there",
    "please give me", "please get me", "please send me",
    "give me", "get me", "send me", "show me",
    "looking for", "searching for",
    "want", "need", "is",
    # Tamil-English mixed
    "enakku", "enaku",  
    "kudunga", "podu", "thaa",
]

CONVERSATIONAL_SUFFIXES = [
    # English phrases
    "is available", "available ah", "available aa", "available a",
    "is available?", "available?", "available",
    "is there", "is there?", "there",
    "do you have", "do you have?",
    "you have", "you have?",
    "please", "pls",
    "iruka", "irukaa", "iruka?", "irukaa?",
    "kidaikuma", "kidaikuma?", "venum", "kedaikuma?",
    "ah", "aa",
]


def extract_product_query(text: str) -> str:
    """
    Strip conversational phrases from user message to extract just the product name part.
    Tries both prefix-first and suffix-first orderings, picks the shorter result.
    
    Examples:
        'i need podi'          → 'podi'
        'do you have laddu'    → 'laddu'
        'mysore pak available' → 'mysore pak'
        'is cake available'    → 'cake'
        'podi'                 → 'podi'
    """
    cleaned = text.strip().lower()
    
    def strip_prefix(s):
        for prefix in CONVERSATIONAL_PREFIXES:
            if s.startswith(prefix):
                s = s[len(prefix):].strip()
                break
        return s
    
    def strip_suffix(s):
        for suffix in CONVERSATIONAL_SUFFIXES:
            if s.endswith(suffix):
                s = s[:-len(suffix)].strip()
                break
        return s
    
    # Try both orderings and pick the shorter (most stripped) result
    option_a = strip_suffix(strip_prefix(cleaned))  # prefix first, then suffix
    option_b = strip_prefix(strip_suffix(cleaned))  # suffix first, then prefix
    
    result = option_a if len(option_a) <= len(option_b) else option_b
    
    # Remove leftover question marks and extra whitespace
    result = result.strip("?!., ")
    
    return result if result else text.strip().lower()


# ==================== 3-LEVEL PRODUCT RESOLUTION ENGINE ====================

def _resolve_product_core(text_clean: str, text_original: str, products: List[Dict]) -> Tuple[Optional[Dict], List[Dict]]:
    """
    Core 3-level product resolution logic. Operates on already-cleaned text.
    """
    
    # ---- LEVEL 0: Known Alias Lookup (cultural name equivalents) ----
    if text_clean in PRODUCT_ALIASES:
        canonical_name = PRODUCT_ALIASES[text_clean].lower()
        # First try exact match with the canonical name
        for product in products:
            if product.get("Product_Name", "").lower() == canonical_name:
                logger.info(f"🎯 L0 ALIAS match: '{text_original}' → '{canonical_name}'")
                return product, []
        
        # If no exact match, use the canonical name for subsequent levels
        logger.info(f"🔄 Alias resolved: '{text_clean}' → '{canonical_name}', continuing search...")
        text_clean = canonical_name
    
    # ---- LEVEL 1: Exact Match (highest priority) ----
    for product in products:
        product_name = product.get("Product_Name", "")
        if text_clean == product_name.lower():
            logger.info(f"🎯 L1 EXACT match: '{text_original}' == '{product_name}'")
            return product, []
    
    # ---- LEVEL 2: Word Boundary & Substring Match (Listing) ----
    boundary_matches = []
    # Sort products by name length descending to prefer longer/more specific matches
    sorted_prods = sorted(products, key=lambda p: len(p.get("Product_Name", "")), reverse=True)
    
    for product in sorted_prods:
        product_name = product.get("Product_Name", "").lower()
        if not product_name:
            continue
        
        # A: Word Boundary match (either direction)
        # 1. Product name in query: e.g. "podi" in "i want oma podi"
        pattern = r'\b' + re.escape(product_name) + r'\b'
        
        # 2. Query in Product name: e.g. "cake" in "Walnut Cake"
        # Only do this if it's a distinct word in the product name
        query_pattern = r'\b' + re.escape(text_clean) + r'\b'
        
        if re.search(pattern, text_clean) or re.search(query_pattern, product_name):
            boundary_matches.append(product)
            logger.info(f"🎯 L2 MATCH: '{product_name}' match found for '{text_clean}'")
            continue # Already matched this product
            
        # B: Substring match for words > 4 letters (as requested)
        if len(text_clean) > 4 and text_clean in product_name:
            boundary_matches.append(product)
            logger.info(f"🎯 L2 SUBSTRING: '{text_clean}' in '{product_name}'")
    
    # Deduplicate matches by Product_ID
    seen_ids = set()
    unique_matches = []
    for m in boundary_matches:
        pid = m.get("Product_ID")
        if pid not in seen_ids:
            unique_matches.append(m)
            seen_ids.add(pid)
    
    if len(unique_matches) == 1:
        return unique_matches[0], []
    elif len(unique_matches) > 1:
        logger.info(f"🔢 L2 Multiple matches: {[p['Product_Name'] for p in unique_matches]}")
        return None, unique_matches
    
    # ---- LEVEL 3: Fuzzy Match (Fallback for typos) ----
    fuzzy_matches = []
    for product in products:
        name = product.get("Product_Name", "").lower()
        # Use full ratio for typos, or partial ratio with very high threshold
        score = fuzz.ratio(text_clean, name)
        if score >= 75: # Lower threshold for full ratio is okay
            fuzzy_matches.append(product)
        else:
            p_score = fuzz.partial_ratio(text_clean, name)
            if p_score >= 90: # Very high threshold for partial match
                fuzzy_matches.append(product)
            
    if len(fuzzy_matches) == 1:
        logger.info(f"🎯 L3 FUZZY match: '{text_original}' ~ '{fuzzy_matches[0]['Product_Name']}'")
        return fuzzy_matches[0], []
    elif len(fuzzy_matches) > 1:
        # Sort by score
        fuzzy_matches.sort(key=lambda p: fuzz.ratio(text_clean, p.get("Product_Name", "").lower()), reverse=True)
        return None, fuzzy_matches
    
    # No match at any level
    logger.info(f"❌ No product match found for: '{text_clean}'")
    return None, []


def resolve_product(text: str, products: List[Dict]) -> Tuple[Optional[Dict], List[Dict]]:
    """
    3-level product resolution engine with natural language understanding.
    
    First tries matching the full text. If that fails and conversational phrases
    are detected ("i need ...", "... is available", etc.), it strips them and
    retries with just the product name part.
    
    Returns:
        Tuple of (matched_product, disambiguation_list)
        - If exactly 1 match: (product_dict, [])
        - If multiple matches: (None, [list of candidates])
        - If no match: (None, [])
    """
    if not text or not products:
        return None, []
    
    text_clean = text.strip().lower()
    
    # First: strip conversational phrases and try cleaned text
    stripped = extract_product_query(text)
    if stripped != text_clean:
        logger.info(f"🔄 Trying product search with cleaned text: '{text}' → '{stripped}'")
        product, candidates = _resolve_product_core(stripped, text, products)
        if product or candidates:
            return product, candidates
    
    # Second: try with the full original text (for direct names like "Mysore Pak")
    product, candidates = _resolve_product_core(text_clean, text, products)
    if product or candidates:
        return product, candidates
    
    return None, []



def detect_all_products(text: str, products: List[Dict]) -> List[Dict]:
    """
    Detect all products mentioned in user message.
    Legacy wrapper around resolve_product() for backward compatibility.
    
    Args:
        text: User message text
        products: List of product dictionaries from STOCK_MASTER
    
    Returns:
        List of matched product dictionaries
    """
    product, candidates = resolve_product(text, products)
    if product:
        return [product]
    return candidates


# ==================== SHOP INFO ====================

def get_shop_info_response(query_type: str) -> str:
    """
    Get shop information response based on query type
    
    Args:
        query_type: Type of query (timing, location, delivery)
    
    Returns:
        Template-based response string
    """
    query_lower = query_type.lower()
    
    if "timing" in query_lower or "open" in query_lower or "close" in query_lower:
        return f"Sir, {Config.SHOP_NAME} is open from {Config.SHOP_TIMING} daily. How can I help you? 😊"
    
    elif "location" in query_lower or "address" in query_lower or "where" in query_lower:
        return f"Sir, we are located at {Config.SHOP_LOCATION}. Anything you need? 😊"
    
    elif "delivery" in query_lower:
        return f"Sir, {Config.DELIVERY_INFO}. What would you like to order? 😊"
    
    else:
        # Generic shop info
        return (
            f"Welcome to {Config.SHOP_NAME}! 🙏\n\n"
            f"📍 Location: {Config.SHOP_LOCATION}\n"
            f"🕐 Timing: {Config.SHOP_TIMING}\n"
            f"🚚 {Config.DELIVERY_INFO}\n\n"
            f"How can I help you today?"
        )


def format_quantity_with_unit(quantity: float, unit_type: str) -> str:
    """
    Format quantity with appropriate unit for display
    
    Args:
        quantity: Numeric quantity
        unit_type: Unit type (KG, PIECE, BOX)
    
    Returns:
        Formatted string like "0.5 kg", "5 pieces", "2 boxes"
    """
    if unit_type == "KG":
        return f"{quantity} kg"
    elif unit_type == "PIECE":
        return f"{int(quantity)} piece{'s' if quantity > 1 else ''}"
    elif unit_type == "BOX":
        return f"{int(quantity)} box{'es' if quantity > 1 else ''}"
    else:
        return f"{quantity} {unit_type.lower()}"
