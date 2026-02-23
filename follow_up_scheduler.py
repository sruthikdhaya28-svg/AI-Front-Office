"""
Follow-up Scheduler for AI Front Office Manager
Handles automated reminders and moves cold leads

Run this script daily (via cron/Task Scheduler) to:
1. Send follow-up reminders for leads that haven't responded
2. Move leads with 0 reminders to LEADS_COLD sheet
"""
import logging
from datetime import datetime, timedelta

from config import Config
from sheets_manager import get_sheets_manager
from send_whatsapp import send_whatsapp_message

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_follow_ups():
    """
    Process follow-ups for all active leads
    
    Logic:
    - If lead is 2+ days old and has reminders left
    - Send follow-up message
    - Decrement reminder count
    - Update last reminder date
    """
    logger.info("🔄 Starting follow-up processing...")
    
    sheets = get_sheets_manager()
    all_leads = sheets.get_all_active_leads()
    
    today = datetime.now().date()
    processed_count = 0
    reminder_sent_count = 0
    
    for lead in all_leads:
        try:
            reminders_left = int(lead.get("No.of_Reminders_Pending", 0))
            
            if reminders_left <= 0:
                continue
            
            # Get last action date
            last_action = lead.get("Last_Action_Date")
            if last_action:
                last_action_date = datetime.strptime(last_action, "%Y-%m-%d").date()
            else:
                # Use lead date if no action date
                lead_date = lead.get("Lead_Date")
                last_action_date = datetime.strptime(lead_date, "%Y-%m-%d").date()
            
            # Check if enough days have passed
            days_since_action = (today - last_action_date).days
            
            if days_since_action >= Config.DAYS_BEFORE_REMINDER:
                # Send reminder
                phone = lead["Phone"]
                product_name = lead["Product_Name"]
                quantity = lead.get("Quantity_Asked", "")
                
                if quantity:
                    message = (
                        f"Hello sir! 🙏 This is a reminder about your enquiry for {product_name}. "
                        f"Quantity: {quantity}. "
                        f"Would you like to proceed with the order? Please reply."
                    )
                else:
                    message = (
                        f"Hello sir! 🙏 We are waiting for quantity confirmation for {product_name}. "
                        f"How many do you need? Please reply."
                    )
                
                # Send WhatsApp message
                status, response = send_whatsapp_message(phone, message)
                
                if status == 200:
                    logger.info(f"✅ Reminder sent for Lead {lead['Lead_ID']}")
                    reminder_sent_count += 1
                    
                    # Update lead in sheet
                    # Find row index
                    all_leads_raw = sheets.leads_sheet.get_all_records()
                    for i, raw_lead in enumerate(all_leads_raw, start=2):
                        if raw_lead["Lead_ID"] == lead["Lead_ID"]:
                            # Update reminders count
                            sheets.leads_sheet.update_cell(
                                i, 
                                sheets.get_column_index("No.of_Reminders_Pending"), 
                                str(reminders_left - 1)
                            )
                            # Update last reminder date
                            sheets.leads_sheet.update_cell(
                                i,
                                sheets.get_column_index("Last_Reminder_Date"),
                                today.strftime("%Y-%m-%d")
                            )
                            break
                else:
                    logger.error(f"❌ Failed to send reminder for Lead {lead['Lead_ID']}")
                
                processed_count += 1
        
        except Exception as e:
            logger.error(f"❌ Error processing lead {lead.get('Lead_ID')}: {e}")
            continue
    
    logger.info(f"✅ Processed {processed_count} leads, sent {reminder_sent_count} reminders")
    return processed_count, reminder_sent_count


def move_cold_leads():
    """
    Move leads with 0 reminders left to LEADS_COLD sheet
    """
    logger.info("❄️ Moving cold leads...")
    
    sheets = get_sheets_manager()
    all_leads = sheets.leads_sheet.get_all_records()
    
    moved_count = 0
    
    # Process in reverse to avoid index issues when deleting
    for i in range(len(all_leads) - 1, -1, -1):
        lead = all_leads[i]
        row_index = i + 2  # +2 for header and 0-indexing
        
        try:
            if lead["Status"] != "ACTIVE":
                continue
            
            reminders_left = int(lead.get("No.of_Reminders_Pending", 0))
            
            if reminders_left == 0:
                # Move to cold
                success = sheets.move_to_cold(lead)
                
                if success:
                    # Delete from active sheet
                    sheets.leads_sheet.delete_rows(row_index)
                    logger.info(f"❄️ Moved lead {lead['Lead_ID']} to COLD")
                    moved_count += 1
        
        except Exception as e:
            logger.error(f"❌ Error moving lead to cold: {e}")
            continue
    
    logger.info(f"✅ Moved {moved_count} leads to COLD")
    return moved_count


def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("AI Front Office Manager - Follow-up Scheduler")
    logger.info(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Process follow-ups
    processed, sent = process_follow_ups()
    
    # Move cold leads
    moved = move_cold_leads()
    
    logger.info("=" * 60)
    logger.info(f"Summary: Processed {processed} leads, Sent {sent} reminders, Moved {moved} to cold")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
