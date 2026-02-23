"""
Test Fraction Parsing - Indian Style Quantities
Tests: 1/2, 3/4, 1 1/2, 2 3/4, etc.
"""

from utils import normalize_quantity, parse_fraction

print("\n" + "=" * 70)
print("🧪 FRACTION PARSING TEST - INDIAN STYLE QUANTITIES")
print("=" * 70 + "\n")

# Test cases: (input, unit_type, expected, description)
test_cases = [
    # Simple fractions
    ("1/2", "KG", 0.5, "Simple: 1/2 kg"),
    ("3/4", "KG", 0.75, "Simple: 3/4 kg"),
    ("1/4", "KG", 0.25, "Simple: 1/4 kg"),
    
    # Mixed numbers (whole + fraction)
    ("1 1/2", "KG", 1.5, "Mixed: 1 1/2 kg (dedh)"),
    ("2 1/2", "KG", 2.5, "Mixed: 2 1/2 kg (dhai)"),
    ("3 1/2", "KG", 3.5, "Mixed: 3 1/2 kg (saadhe teen)"),
    ("1 1/4", "KG", 1.25, "Mixed: 1 1/4 kg (sava)"),
    ("2 3/4", "KG", 2.75, "Mixed: 2 3/4 kg (paune teen)"),
    
    # With context
    ("I need 1/2 kg", "KG", 0.5, "Context: I need 1/2 kg"),
    ("Give me 1 1/2 kg", "KG", 1.5, "Context: Give me 1 1/2 kg"),
    ("1/2 kg venum", "KG", 0.5, "Tamil: 1/2 kg venum"),
    ("1 1/2 kg kudunga", "KG", 1.5, "Tamil: 1 1/2 kg kudunga"),
    
    # Edge cases
    ("1/2kg", "KG", 0.5, "No space: 1/2kg"),
    ("1 1/2kg", "KG", 1.5, "No space: 1 1/2kg"),
    ("  1/2  ", "KG", 0.5, "Extra spaces: '  1/2  '"),
]

passed = 0
failed = 0
failures = []

for input_text, unit_type, expected, description in test_cases:
    result = normalize_quantity(input_text, unit_type)
    
    if result == expected:
        print(f"✅ PASS: {description}")
        print(f"   Input: '{input_text}' → Output: {result} kg")
        passed += 1
    else:
        print(f"❌ FAIL: {description}")
        print(f"   Input: '{input_text}' → Expected: {expected}, Got: {result}")
        failed += 1
        failures.append((description, input_text, expected, result))

print("\n" + "=" * 70)
print("📊 RESULTS")
print("=" * 70)
print(f"\n✅ Passed: {passed}/{len(test_cases)}")
print(f"❌ Failed: {failed}/{len(test_cases)}")
print(f"📈 Pass Rate: {(passed/len(test_cases)*100):.1f}%")

if failures:
    print("\n🔴 FAILURES:")
    for desc, inp, exp, got in failures:
        print(f"\n  • {desc}")
        print(f"    Input: '{inp}'")
        print(f"    Expected: {exp}")
        print(f"    Got: {got}")
else:
    print("\n🎉 ALL FRACTION FORMATS WORKING!")

# Test parse_fraction directly
print("\n" + "=" * 70)
print("🔍 DIRECT PARSE_FRACTION TESTS")
print("=" * 70 + "\n")

direct_tests = [
    ("1/2", 0.5),
    ("3/4", 0.75),
    ("1 1/2", 1.5),
    ("2 3/4", 2.75),
    ("abc", None),  # Invalid
]

for inp, expected in direct_tests:
    result = parse_fraction(inp)
    status = "✅" if result == expected else "❌"
    print(f"{status} parse_fraction('{inp}') → {result} (expected: {expected})")

print("\n" + "=" * 70 + "\n")
