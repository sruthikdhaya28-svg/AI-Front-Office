from sheets_manager import get_sheets_manager
import logging

# Enable debug logging for sheets_manager
logging.basicConfig(level=logging.INFO)

def debug_stats():
    try:
        sheets = get_sheets_manager()
        print("Fetching stats...")
        # We call the internal logic to see where it fails
        
        try:
            active_list = sheets.leads_sheet.get_all_records()
            print(f"Active Leads: {len(active_list)}")
        except Exception as e:
            print(f"Error fetching Active leads: {e}")
            
        try:
            confirmed_list = sheets.confirmed_sheet.get_all_records()
            print(f"Confirmed Leads: {len(confirmed_list)}")
        except Exception as e:
            print(f"Error fetching Confirmed leads: {e}")
            
        try:
            closed_list = sheets.closed_sheet.get_all_records()
            print(f"Closed Leads: {len(closed_list)}")
        except Exception as e:
            print(f"Error fetching Closed leads: {e}")
            
        stats = sheets.get_dashboard_stats()
        print(f"Result Stats: {stats}")
        
    except Exception as e:
        print(f"GLOBAL ERROR: {e}")

if __name__ == "__main__":
    debug_stats()
