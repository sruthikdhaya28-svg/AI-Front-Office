from utils import resolve_product
import logging

logging.basicConfig(level=logging.INFO)

products = [
    {'Product_ID': 'P065', 'Product_Name': 'Suryakala', 'Base_Price': 500}
]

def test(query):
    print(f"\nTesting query: '{query}'")
    match, candidates = resolve_product(query, products)
    if match:
        print(f"✅ MATCH: {match['Product_Name']}")
    elif candidates:
        print(f"🔢 CANDIDATES: {[p['Product_Name'] for p in candidates]}")
    else:
        print("❌ NO MATCH")

test("surya")
test("kala")
test("Suryakala")
test("i want surya")
