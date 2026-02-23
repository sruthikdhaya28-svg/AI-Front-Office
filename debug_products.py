"""
Quick debug script to check Google Sheets products
"""
from sheets_manager import get_sheets_manager

sheets = get_sheets_manager()
products = sheets.get_products()

print(f"\n✅ Total products loaded: {len(products)}\n")
print("=" * 60)
print("PRODUCT LIST:")
print("=" * 60)

for i, p in enumerate(products, 1):
    product_name = p.get("Product_Name", "N/A")
    unit_type = p.get("Unit_Type", "N/A")
    price = p.get("Base_Price", "N/A")
    print(f"{i}. {product_name} - {unit_type} - ₹{price}")

print("\n" + "=" * 60)
print("TESTING PRODUCT DETECTION:")
print("=" * 60)

test_queries = ["biscuit", "mysore pak", "laddu", "mixture"]

for query in test_queries:
    matches = sheets.find_all_matching_products(query)
    if matches:
        print(f"\n✅ '{query}' → Found {len(matches)} match(es):")
        for m in matches:
            print(f"   - {m.get('Product_Name')}")
    else:
        print(f"\n❌ '{query}' → No matches found")

print("\n" + "=" * 60)
