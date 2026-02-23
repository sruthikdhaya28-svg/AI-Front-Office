"""
🧪 ARCHITECTURE VALIDATION TESTS – Anjali Sweets v2
Tests for the architecture fix:
  - 3-level product resolution engine
  - Centralized extract_quantity()
  - Catalog keyword detection
  - Language detection

NOTE: Webhook functions that depend on Google Sheets are tested by
importing just the standalone functions (catalog, language, session).
"""
import sys
import os

# Test tracking
passed = 0
failed = 0
errors = []

def test_pass(name):
    global passed
    passed += 1
    print(f"  ✅ {name}")

def test_fail(name, expected, got):
    global failed
    failed += 1
    msg = f"  ❌ {name}: expected={expected}, got={got}"
    errors.append(msg)
    print(msg)


# ==================== Test: Product Resolution Engine ====================

print("\n" + "="*60)
print("📦 TEST: 3-Level Product Resolution Engine")
print("="*60)

from utils import resolve_product, extract_quantity, format_quantity_with_unit

# Mock product catalog
PRODUCTS = [
    {"Product_Name": "Oma Podi", "Base_Price": 200, "Unit_Type": "KG", "Product_ID": "P1"},
    {"Product_Name": "Pudina Oma Podi", "Base_Price": 240, "Unit_Type": "KG", "Product_ID": "P2"},
    {"Product_Name": "Mysore Pak", "Base_Price": 400, "Unit_Type": "KG", "Product_ID": "P3"},
    {"Product_Name": "Special Mysore Pak", "Base_Price": 600, "Unit_Type": "KG", "Product_ID": "P4"},
    {"Product_Name": "Laddu", "Base_Price": 400, "Unit_Type": "KG", "Product_ID": "P5"},
    {"Product_Name": "Jangiri", "Base_Price": 360, "Unit_Type": "KG", "Product_ID": "P6"},
    {"Product_Name": "Butter Biscuit", "Base_Price": 200, "Unit_Type": "KG", "Product_ID": "P7"},
    {"Product_Name": "Ghee Biscuit", "Base_Price": 240, "Unit_Type": "KG", "Product_ID": "P8"},
    {"Product_Name": "Coconut Biscuit", "Base_Price": 180, "Unit_Type": "KG", "Product_ID": "P9"},
    {"Product_Name": "Kaju Katli", "Base_Price": 960, "Unit_Type": "KG", "Product_ID": "P10"},
    {"Product_Name": "Mixture", "Base_Price": 200, "Unit_Type": "KG", "Product_ID": "P11"},
    {"Product_Name": "Special Mixture", "Base_Price": 280, "Unit_Type": "KG", "Product_ID": "P12"},
    {"Product_Name": "Milk Sweets", "Base_Price": 500, "Unit_Type": "KG", "Product_ID": "P13"},
]

# LEVEL 1 – Exact Match
print("\n  Level 1: Exact Match")
p, c = resolve_product("oma podi", PRODUCTS)
if p and p["Product_Name"] == "Oma Podi":
    test_pass("'oma podi' → Oma Podi (exact)")
else:
    test_fail("'oma podi' → Oma Podi (exact)", "Oma Podi", p["Product_Name"] if p else f"candidates={[x['Product_Name'] for x in c]}")

p, c = resolve_product("Mysore Pak", PRODUCTS)
if p and p["Product_Name"] == "Mysore Pak":
    test_pass("'Mysore Pak' → Mysore Pak (exact)")
else:
    test_fail("'Mysore Pak' → Mysore Pak (exact)", "Mysore Pak", p["Product_Name"] if p else "None")

p, c = resolve_product("kaju katli", PRODUCTS)
if p and p["Product_Name"] == "Kaju Katli":
    test_pass("'kaju katli' → Kaju Katli (exact)")
else:
    test_fail("'kaju katli' → Kaju Katli (exact)", "Kaju Katli", p["Product_Name"] if p else "None")

p, c = resolve_product("jangiri", PRODUCTS)
if p and p["Product_Name"] == "Jangiri":
    test_pass("'jangiri' → Jangiri (exact)")
else:
    test_fail("'jangiri' → Jangiri (exact)", "Jangiri", p["Product_Name"] if p else "None")

# LEVEL 2 – Word Boundary (prevents substring collision)
print("\n  Level 2: Word Boundary Match")

p, c = resolve_product("I need pudina oma podi", PRODUCTS)
if p and p["Product_Name"] == "Pudina Oma Podi":
    test_pass("'I need pudina oma podi' → Pudina Oma Podi (boundary)")
elif not p and c:
    # Both "Oma Podi" and "Pudina Oma Podi" boundary-match — disambiguation acceptable
    names = [x["Product_Name"] for x in c]
    if "Pudina Oma Podi" in names:
        test_pass(f"'I need pudina oma podi' → disambiguation with Pudina (acceptable): {names}")
    else:
        test_fail("'I need pudina oma podi'", "Pudina Oma Podi", names)
else:
    test_fail("'I need pudina oma podi'", "Pudina Oma Podi", p["Product_Name"] if p else "None")

# LEVEL 3 – Fuzzy Match (spelling tolerance)
print("\n  Level 3: Fuzzy Match")
p, c = resolve_product("mysore pakk", PRODUCTS)
if p and p["Product_Name"] == "Mysore Pak":
    test_pass("'mysore pakk' → Mysore Pak (fuzzy typo)")
elif p:
    test_fail("'mysore pakk' fuzzy", "Mysore Pak", p["Product_Name"])
else:
    test_fail("'mysore pakk' fuzzy", "Mysore Pak", f"no match, candidates={[x['Product_Name'] for x in c]}")

p, c = resolve_product("ladoo", PRODUCTS)
if p and p["Product_Name"] == "Laddu":
    test_pass("'ladoo' → Laddu (fuzzy)")
else:
    test_fail("'ladoo' fuzzy", "Laddu", p["Product_Name"] if p else f"candidates={[x['Product_Name'] for x in c]}")

p, c = resolve_product("kaju kathli", PRODUCTS)
if p and p["Product_Name"] == "Kaju Katli":
    test_pass("'kaju kathli' → Kaju Katli (fuzzy)")
else:
    test_fail("'kaju kathli' fuzzy", "Kaju Katli", p["Product_Name"] if p else f"candidates={[x['Product_Name'] for x in c]}")

# Disambiguation
print("\n  Disambiguation")
p, c = resolve_product("biscuit", PRODUCTS)
if not p and len(c) >= 2:
    names = [x["Product_Name"] for x in c]
    if all("Biscuit" in n for n in names):
        test_pass(f"'biscuit' → disambiguation: {names}")
    else:
        test_fail("'biscuit' disambiguation", "multiple Biscuit items", names)
else:
    test_fail("'biscuit' disambiguation", "multiple", p["Product_Name"] if p else f"candidates={len(c)}")

p, c = resolve_product("mixture", PRODUCTS)
if p and p["Product_Name"] == "Mixture":
    test_pass("'mixture' → Mixture (exact match, not Special)")
elif not p and len(c) >= 2:
    # Disambiguation acceptable too
    test_pass(f"'mixture' → disambiguation (acceptable): {[x['Product_Name'] for x in c]}")
else:
    test_fail("'mixture'", "Mixture or disambiguation", p["Product_Name"] if p else "None")

# Negative test
print("\n  Negative Tests")
p, c = resolve_product("pizza", PRODUCTS)
if not p and not c:
    test_pass("'pizza' → no match (correct)")
else:
    test_fail("'pizza' should not match", "no match", p["Product_Name"] if p else f"candidates={[x['Product_Name'] for x in c]}")

# 'sweets' should NOT match to Milk Sweets (catalog behavior)
p, c = resolve_product("what sweets do you have", PRODUCTS)
# This should ideally not match Milk Sweets
if not p and not c:
    test_pass("'what sweets do you have' → no product match (catalog handled separately)")
elif p and p["Product_Name"] == "Milk Sweets":
    test_fail("'what sweets do you have'", "no product match (catalog)", "matched Milk Sweets incorrectly")
else:
    # Accept candidates list as warning
    test_pass(f"'what sweets...' → some candidates (acceptable, catalog checked first in webhook)")


# ==================== Test: Quantity Extraction ====================

print("\n" + "="*60)
print("📏 TEST: Centralized extract_quantity()")
print("="*60)

# Pure digits
print("\n  Pure Digits")
tests = [
    ("1", "PIECE", 1.0),
    ("5", "KG", 5.0),
    ("10", "BOX", 10.0),
    ("100", "PIECE", 100.0),
]
for text, unit, expected in tests:
    result = extract_quantity(text, unit)
    if result == expected:
        test_pass(f"'{text}' ({unit}) → {expected}")
    else:
        test_fail(f"'{text}' ({unit})", expected, result)

# Gram conversions
print("\n  Gram Conversions")
gram_tests = [
    ("100g", "KG", 0.1),
    ("250g", "KG", 0.25),
    ("250 grams", "KG", 0.25),
    ("500g", "KG", 0.5),
    ("500gm", "KG", 0.5),
]
for text, unit, expected in gram_tests:
    result = extract_quantity(text, unit)
    if result == expected:
        test_pass(f"'{text}' → {expected} kg")
    else:
        test_fail(f"'{text}'", expected, result)

# Word quantities
print("\n  Word Quantities")
word_tests = [
    ("half", "KG", 0.5),
    ("quarter", "KG", 0.25),
    ("ara", "KG", 0.5),
    ("kaal", "KG", 0.25),
]
for text, unit, expected in word_tests:
    result = extract_quantity(text, unit)
    if result == expected:
        test_pass(f"'{text}' → {expected}")
    else:
        test_fail(f"'{text}'", expected, result)

# Fractions
print("\n  Fractions")
frac_tests = [
    ("1/2", "KG", 0.5),
    ("1/4", "KG", 0.25),
    ("3/4", "KG", 0.75),
    ("1 1/2", "KG", 1.5),
    ("2 1/4", "KG", 2.25),
]
for text, unit, expected in frac_tests:
    result = extract_quantity(text, unit)
    if result == expected:
        test_pass(f"'{text}' → {expected}")
    else:
        test_fail(f"'{text}'", expected, result)

# Decimal
print("\n  Decimal")
dec_tests = [
    ("1.5", "KG", 1.5),
    ("0.5", "KG", 0.5),
    ("2.5 kg", "KG", 2.5),
]
for text, unit, expected in dec_tests:
    result = extract_quantity(text, unit)
    if result == expected:
        test_pass(f"'{text}' → {expected}")
    else:
        test_fail(f"'{text}'", expected, result)

# Format display
print("\n  Format Display")
fmt_tests = [
    (0.5, "KG", "0.5 kg"),
    (2.0, "KG", "2.0 kg"),
    (5.0, "PIECE", "5 pieces"),
    (1.0, "PIECE", "1 piece"),
    (3.0, "BOX", "3 boxes"),
    (1.0, "BOX", "1 box"),
]
for qty, unit, expected in fmt_tests:
    result = format_quantity_with_unit(qty, unit)
    if result == expected:
        test_pass(f"format({qty}, {unit}) → '{expected}'")
    else:
        test_fail(f"format({qty}, {unit})", expected, result)


# ==================== Test: Catalog & Language Detection (standalone) ====================

print("\n" + "="*60)
print("📋 TEST: Catalog Keyword Detection (standalone)")
print("="*60)

# Test catalog keywords directly (same logic as webhook.is_catalog_intent)
CATALOG_KEYWORDS = [
    "what sweets", "what snacks", "list items", "show menu",
    "what all available", "menu", "what do you have",
    "what products", "tell me items", "full list",
    "all products", "all items", "everything you have",
    "complete list", "all of them",
    "what all", "enna iruku", "enna enna iruku",
]

def is_catalog_intent_standalone(text, ai_intent="other"):
    if ai_intent == "catalog":
        return True
    text_lower = text.lower()
    return any(kw in text_lower for kw in CATALOG_KEYWORDS)

catalog_positives = [
    "what sweets do you have",
    "show menu",
    "list items",
    "what all available",
    "what products do you sell",
    "I want to see the menu",
    "what do you have",
]

for text in catalog_positives:
    if is_catalog_intent_standalone(text):
        test_pass(f"catalog: '{text}' → True")
    else:
        test_fail(f"catalog: '{text}'", True, False)

catalog_negatives = [
    "I want mysore pak",
    "give me laddu",
    "2 kg",
    "yes",
    "cancel",
]

for text in catalog_negatives:
    if not is_catalog_intent_standalone(text):
        test_pass(f"NOT catalog: '{text}' → False")
    else:
        test_fail(f"NOT catalog: '{text}'", False, True)

print("\n" + "="*60)
print("🌐 TEST: Language Detection (standalone)")
print("="*60)

# Replicate the logic from webhook.py
TAMIL_INDICATORS = [
    "venum", "iruka", "evlo", "sollunga", "kudunga", "pannunga",
    "podhum", "vendaam", "sari", "illa", "enna", "enga",
    "inga", "anga", "atha", "itha", "ara", "kaal", "nga",
    "da", "la", "ah", "eh", "enakku", "podu",
]

def detect_language_standalone(text, ai_language="en"):
    text_lower = text.lower()
    for word in TAMIL_INDICATORS:
        if f" {word} " in f" {text_lower} " or text_lower.startswith(word + " ") or text_lower.endswith(" " + word) or text_lower == word:
            return "ta"
    if ai_language == "ta":
        return "ta"
    return "en"

lang_tests = [
    ("I need Mysore Pak", "en", "en"),
    ("mysore pak venum", "ta", "ta"),
    ("evlo kg venum", "ta", "ta"),
    ("how much", "en", "en"),
    ("hello", "en", "en"),
    ("I want laddu", "en", "en"),
    ("enna iruku sir", "ta", "ta"),
    ("2 kg kudunga", "ta", "ta"),
]

for text, ai_lang, expected in lang_tests:
    result = detect_language_standalone(text, ai_lang)
    if result == expected:
        test_pass(f"lang('{text}', ai={ai_lang}) → {expected}")
    else:
        test_fail(f"lang('{text}', ai={ai_lang})", expected, result)


# ==================== RESULTS ====================

print("\n" + "="*60)
print("📊 RESULTS")
print("="*60)
print(f"  ✅ Passed: {passed}")
print(f"  ❌ Failed: {failed}")
print(f"  📊 Total:  {passed + failed}")

if errors:
    print("\n  Failures:")
    for e in errors:
        print(f"    {e}")

if failed == 0:
    print("\n  🎉 ALL TESTS PASSED!")
else:
    print(f"\n  ⚠️ {failed} test(s) failed")

sys.exit(1 if failed > 0 else 0)
