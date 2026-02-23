from sheets_manager import get_sheets_manager
import logging

logging.basicConfig(level=logging.INFO)

def debug_inventory():
    try:
        sheets = get_sheets_manager()
        print(f"Opening sheet: {sheets.sheet.title}")
        print(f"Worksheet: {sheets.stock_sheet.title}")
        
        records = sheets.stock_sheet.get_all_records()
        print(f"Raw records count: {len(records)}")
        if records:
            print("First 5 records:")
            for r in records[:5]:
                print(r)
        else:
            print("No records found (or sheet is empty/missing headers)")
            
        products = sheets.get_products()
        print(f"Processed products count: {len(products)}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    debug_inventory()
