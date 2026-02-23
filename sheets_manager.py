"""
Google Sheets Manager for AI Front Office Manager
Handles all Google Sheets operations with caching and error handling
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import uuid
import logging
from typing import Optional, List, Dict, Tuple

from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SheetsManager:
    """Manages all Google Sheets operations"""
    
    def __init__(self):
        """Initialize Google Sheets connection"""
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            
            creds = Credentials.from_service_account_file(
                Config.GOOGLE_CREDENTIALS_FILE, 
                scopes=scopes
            )
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open(Config.GOOGLE_SHEET_NAME)
            
            # Get worksheets (LEADS_ACTIVE and STOCK_MASTER are required)
            self.leads_sheet = self.sheet.worksheet("LEADS_ACTIVE")
            self.stock_sheet = self.sheet.worksheet("STOCK_MASTER")
            
            # Optional worksheets — create if missing
            try:
                self.cold_sheet = self.sheet.worksheet("LEADS_COLD")
            except gspread.exceptions.WorksheetNotFound:
                logger.warning("⚠️ LEADS_COLD worksheet not found — creating it")
                self.cold_sheet = self.sheet.add_worksheet(title="LEADS_COLD", rows=100, cols=15)
            
            try:
                self.closed_sheet = self.sheet.worksheet("LEADS_CLOSED")
            except gspread.exceptions.WorksheetNotFound:
                logger.warning("⚠️ LEADS_CLOSED worksheet not found — creating it")
                self.closed_sheet = self.sheet.add_worksheet(title="LEADS_CLOSED", rows=100, cols=15)
                # Add headers
                headers = [
                    "Lead_ID", "Customer_Name", "Phone", "Customer_Message",
                    "Product_ID", "Product_Name", "Quantity_Asked", "Price_Shown", 
                    "Total_Amount", "Lead_Date", "Lead_Time", "Status", "Last_Action_Date"
                ]
                self.closed_sheet.append_row(headers)
                
            try:
                self.confirmed_sheet = self.sheet.worksheet("LEADS_CONFIRMED")
            except gspread.exceptions.WorksheetNotFound:
                logger.warning("⚠️ LEADS_CONFIRMED worksheet not found — creating it")
                self.confirmed_sheet = self.sheet.add_worksheet(title="LEADS_CONFIRMED", rows=100, cols=15)
                # Add headers
                headers = [
                    "Lead_ID", "Customer_Name", "Phone", "Customer_Message",
                    "Product_ID", "Product_Name", "Quantity_Asked", "Price_Shown", 
                    "Total_Amount", "Lead_Date", "Lead_Time", "Status", "Last_Action_Date"
                ]
                self.confirmed_sheet.append_row(headers)
            
            # Cache for products
            self._products_cache = None
            self._keyword_map_cache = None
            
            logger.info("✅ Google Sheets connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Google Sheets: {e}")
            raise
    
    # ==================== PRODUCT MANAGEMENT ====================

    def get_products(self, use_cache: bool = True) -> List[Dict]:
        """
        Get all products from STOCK_MASTER sheet with caching
        """
        if use_cache and self._products_cache:
            return self._products_cache
            
        try:
            products = self.stock_sheet.get_all_records()
            # Basic validation: ensure key fields exist
            valid_products = []
            for p in products:
                if p.get("Product_ID") and p.get("Product_Name"):
                    valid_products.append(p)
            
            self._products_cache = valid_products
            return valid_products
        except Exception as e:
            logger.error(f"❌ Error fetching products: {e}")
            return []

    def add_product(self, data: Dict) -> bool:
        """
        Add a new product to STOCK_MASTER
        """
        try:
            # Ensure headers exist
            headers = self.stock_sheet.row_values(1)
            if not headers:
                headers = ["Product_ID", "Product_Name", "Brand", "Unit_Type", "Base_Price", "Category", "Stock_Quantity", "Last_Updated"]
                self.stock_sheet.append_row(headers)
            
            # Generate Product_ID if missing
            if not data.get("Product_ID"):
                existing = self.get_products()
                max_id = 0
                for p in existing:
                    try:
                        id_num = int(str(p.get("Product_ID", "P0")).replace("P", ""))
                        if id_num > max_id: max_id = id_num
                    except: pass
                data["Product_ID"] = f"P{str(max_id + 1).zfill(3)}"

            row = []
            for h in headers:
                val = data.get(h, "")
                if h == "Last_Updated":
                    val = datetime.now().strftime("%d-%m-%Y")
                row.append(val)
                
            self.stock_sheet.append_row(row)
            self._products_cache = None # Invalidate cache
            return True
        except Exception as e:
            logger.error(f"❌ Error adding product: {e}")
            return False

    def update_product(self, product_name: str, data: Dict) -> bool:
        """
        Update an existing product in STOCK_MASTER
        """
        try:
            records = self.stock_sheet.get_all_records()
            headers = self.stock_sheet.row_values(1)
            
            for i, record in enumerate(records):
                if record.get("Product_Name") == product_name:
                    row_index = i + 2
                    for col_name, value in data.items():
                        if col_name in headers:
                            col_index = headers.index(col_name) + 1
                            self.stock_sheet.update_cell(row_index, col_index, value)
                    
                    # Update timestamp
                    if "Last_Updated" in headers:
                        col_index = headers.index("Last_Updated") + 1
                        self.stock_sheet.update_cell(row_index, col_index, datetime.now().strftime("%d-%m-%Y"))
                    
                    self._products_cache = None
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Error updating product: {e}")
            return False

    def delete_product(self, product_name: str) -> bool:
        """
        Delete a product from STOCK_MASTER
        """
        try:
            records = self.stock_sheet.get_all_records()
            for i, record in enumerate(records):
                if record.get("Product_Name") == product_name:
                    self.stock_sheet.delete_rows(i + 2)
                    self._products_cache = None
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting product: {e}")
            return False

    def get_keyword_map(self) -> Dict[str, str]:
        """
        Get map of keywords to Product IDs with caching
        """
        if self._keyword_map_cache:
            return self._keyword_map_cache
            
        try:
            products = self.get_products()
            keyword_map = {}
            
            for p in products:
                pid = p.get("Product_ID")
                # Add product name itself
                name = p.get("Product_Name", "").lower()
                keyword_map[name] = pid
                
                # Add keywords
                keywords = str(p.get("Keywords", "")).split(",")
                for k in keywords:
                    clean_k = k.strip().lower()
                    if clean_k:
                        keyword_map[clean_k] = pid
                        
            self._keyword_map_cache = keyword_map
            return keyword_map
        except Exception as e:
            logger.error(f"❌ Error building keyword map: {e}")
            return {}

    def find_all_matching_products(self, query: str) -> List[Dict]:
        """
        Find products matching query (Exact -> Word Boundary -> Fuzzy)
        """
        # This is largely handled by utils.py now, but kept for compatibility
        # if needed by webhook.py legacy paths
        return []

    def get_column_index(self, col_name: str, sheet=None) -> int:
        """
        Get 1-based column index for a given column name
        """
        try:
            target_sheet = sheet or self.leads_sheet
            headers = target_sheet.row_values(1)
            return headers.index(col_name) + 1
        except ValueError:
            logger.error(f"Column '{col_name}' not found")
            return -1
        except Exception as e:
            logger.error(f"Error getting column index: {e}")
            return -1

    def get_all_active_leads(self, phone: Optional[str] = None) -> List[Dict]:
        """
        Get all active leads, optionally filtered by phone number
        """
        try:
            all_leads = self.leads_sheet.get_all_records()
            
            if phone:
                leads = [
                    lead for lead in all_leads 
                    if str(lead.get("Phone")) == phone and lead["Status"] == "ACTIVE"
                ]
            else:
                leads = [lead for lead in all_leads if lead["Status"] == "ACTIVE"]
            
            return leads
        except Exception as e:
            logger.error(f"❌ Error getting active leads: {e}")
            return []

    def create_active_lead(self, phone: str, product: Dict) -> Optional[str]:
        """
        Create an ACTIVE lead in LEADS_ACTIVE when customer enquires about a product.
        
        Returns:
            lead_id string on success, None on failure
        """
        try:
            now = datetime.now()
            lead_id = now.strftime("%Y%m%d%H%M%S")

            lead_row = [
                lead_id,
                "WhatsApp Customer",              # Customer_Name
                phone,                             # Phone
                "",                                # Customer_Message
                product.get("Product_ID", ""),     # Product_ID
                product.get("Product_Name", ""),   # Product_Name
                "",                                # Quantity_Asked (not known yet)
                product.get("Base_Price", ""),      # Price_Shown
                "",                                # Total_Amount (not known yet)
                now.strftime("%d-%m-%Y"),           # Lead_Date
                now.strftime("%H:%M:%S"),           # Lead_Time
                "ACTIVE",                          # Status
                now.strftime("%d-%m-%Y"),           # Last_Action_Date
            ]

            self.leads_sheet.append_row(lead_row)
            logger.info(f"✅ Created ACTIVE lead {lead_id} in LEADS_ACTIVE for {product.get('Product_Name')}")
            return lead_id

        except Exception as e:
            logger.error(f"❌ Error creating active lead: {e}")
            return None

    def cancel_active_lead(self, lead_id: str) -> bool:
        """
        Update an ACTIVE lead's status to CANCELLED in LEADS_ACTIVE.
        """
        try:
            all_leads = self.leads_sheet.get_all_records()
            for i, lead in enumerate(all_leads):
                if str(lead.get("Lead_ID", "")).strip() == str(lead_id).strip():
                    row_index = i + 2  # +1 for header, +1 for 1-indexed
                    self._update_cell(self.leads_sheet, row_index, "Status", "CANCELLED")
                    self._update_cell(self.leads_sheet, row_index, "Last_Action_Date", datetime.now().strftime("%d-%m-%Y"))
                    logger.info(f"✅ Lead {lead_id} status updated to CANCELLED in LEADS_ACTIVE")
                    return True

            logger.warning(f"⚠️ Lead {lead_id} not found in LEADS_ACTIVE for cancellation")
            return False

        except Exception as e:
            logger.error(f"❌ Error cancelling active lead: {e}")
            return False

    def update_active_lead_quantity(self, lead_id: str, quantity: float, total: float) -> bool:
        """
        Update Quantity_Asked and Total_Amount for an ACTIVE lead in LEADS_ACTIVE.
        """
        try:
            all_leads = self.leads_sheet.get_all_records()
            for i, lead in enumerate(all_leads):
                if str(lead.get("Lead_ID", "")).strip() == str(lead_id).strip():
                    row_index = i + 2
                    self._update_cell(self.leads_sheet, row_index, "Quantity_Asked", str(quantity))
                    self._update_cell(self.leads_sheet, row_index, "Total_Amount", str(total))
                    self._update_cell(self.leads_sheet, row_index, "Last_Action_Date", datetime.now().strftime("%d-%m-%Y"))
                    logger.info(f"✅ Updated lead {lead_id} quantity={quantity}, total=₹{total}")
                    return True

            logger.warning(f"⚠️ Lead {lead_id} not found for quantity update")
            return False

        except Exception as e:
            logger.error(f"❌ Error updating active lead quantity: {e}")
            return False

    # ... (skipping get_existing_product_lead, get_open_quantity_lead, create_lead, update_lead_quantity, update_lead_total) ...

    def update_lead_status(self, row_index: int, status: str) -> bool:
        """
        Update status for a lead in active sheet (helper for older method name)
        """
        try:
            col_index = self.get_column_index("Status")
            self.leads_sheet.update_cell(row_index, col_index, status)
            logger.info(f"✅ Updated status to {status} for row {row_index}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating status: {e}")
            return False

    # ... (skipping update_lead_field, get_lead_for_confirmation, move_to_cold) ...
    
    def create_confirmed_lead(self, phone: str, product: Dict, quantity: float, total: float) -> bool:
        """
        Create a COMPLETE lead in LEADS_CONFIRMED at confirmation time.
        """
        try:
            now = datetime.now()
            lead_id = now.strftime("%Y%m%d%H%M%S")
            
            lead_row = [
                lead_id,
                "WhatsApp Customer",        # Customer_Name
                phone,                       # Phone
                "",                          # Customer_Message
                product.get("Product_ID", ""),  # Product_ID
                product.get("Product_Name", ""),  # Product_Name
                str(quantity),               # Quantity_Asked
                product.get("Base_Price", ""),  # Price_Shown
                str(total),                  # Total_Amount
                now.strftime("%d-%m-%Y"),    # Lead_Date
                now.strftime("%H:%M:%S"),    # Lead_Time
                "CONFIRMED",                 # Status
                now.strftime("%d-%m-%Y"),    # Last_Action_Date
            ]
            
            self.confirmed_sheet.append_row(lead_row)
            logger.info(f"✅ Created confirmed lead {lead_id} in LEADS_CONFIRMED")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating confirmed lead: {e}")
            return False
            
    # ... (skipping admin methods) ...

    def get_all_leads(self, status_filter: Optional[str] = None) -> List[Dict]:
        """
        Get all leads from ACTIVE and CONFIRMED sheets
        """
        try:
            leads = []
            
            # Fetch from ACTIVE
            if status_filter != "CONFIRMED":
                active_leads = self.leads_sheet.get_all_records()
                leads.extend(active_leads)
            
            # Fetch from CONFIRMED
            if status_filter != "ACTIVE":
                confirmed_leads = self.confirmed_sheet.get_all_records()
                leads.extend(confirmed_leads)
                
            if status_filter:
                leads = [lead for lead in leads if lead.get("Status") == status_filter]
            
            return leads
            
        except Exception as e:
            logger.error(f"❌ Error getting aggregated leads: {e}")
            return []

    # ... (skipping get_closed_leads) ...

    def move_lead_to_closed(self, lead_id: str) -> bool:
        """
        Move a lead from LEADS_ACTIVE or LEADS_CONFIRMED to LEADS_CLOSED
        """
        try:
            # Check Confirmed Sheet First (most likely)
            confirmed_leads = self.confirmed_sheet.get_all_records()
            for i, lead in enumerate(confirmed_leads):
                # Robust comparison: Convert both to string and strip whitespace
                if str(lead.get("Lead_ID", "")).strip() == str(lead_id).strip():
                    self._move_row(self.confirmed_sheet, i + 2, lead, "CLOSED")
                    return True
            
            # Check Active Sheet
            active_leads = self.leads_sheet.get_all_records()
            for i, lead in enumerate(active_leads):
                if str(lead.get("Lead_ID", "")).strip() == str(lead_id).strip():
                    self._move_row(self.leads_sheet, i + 2, lead, "CLOSED")
                    return True
            
            logger.warning(f"⚠️ Lead not found for closing: {lead_id}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error moving lead to closed: {e}")
            return False

    def update_lead_status_by_id(self, lead_id: str, new_status: str) -> bool:
        """
        Update lead status by lead ID. Handles moving between sheets.
        """
        try:
            # Status change triggers move?
            if new_status == "CONFIRMED":
                # Move from ACTIVE -> CONFIRMED
                active_leads = self.leads_sheet.get_all_records()
                for i, lead in enumerate(active_leads):
                    if str(lead.get("Lead_ID", "")).strip() == str(lead_id).strip():
                        self._move_row(self.leads_sheet, i + 2, lead, "CONFIRMED", target_sheet=self.confirmed_sheet)
                        return True
            
            elif new_status == "CLOSED":
                return self.move_lead_to_closed(lead_id)
            
            # Only status update in place (ACTIVE -> ACTIVE or CONFIRMED -> CONFIRMED)
             # Check Active first
            active_leads = self.leads_sheet.get_all_records()
            for i, lead in enumerate(active_leads):
                if str(lead.get("Lead_ID", "")).strip() == str(lead_id).strip():
                    self._update_cell(self.leads_sheet, i + 2, "Status", new_status)
                    return True

            # Check Confirmed
            confirmed_leads = self.confirmed_sheet.get_all_records()
            for i, lead in enumerate(confirmed_leads):
                if str(lead.get("Lead_ID", "")).strip() == str(lead_id).strip():
                    self._update_cell(self.confirmed_sheet, i + 2, "Status", new_status)
                    return True
                    
            logger.warning(f"⚠️ Lead not found for status update: {lead_id}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error updating lead status: {e}")
            return False

    def _update_cell(self, sheet, row_index, col_name, value):
        headers = sheet.row_values(1)
        if col_name in headers:
            col_index = headers.index(col_name) + 1
            sheet.update_cell(row_index, col_index, value)

    def _move_row(self, source_sheet, row_index, lead_data, new_status, target_sheet=None):
        """Helper to move row to target sheet (default: CLOSED)"""
        if target_sheet is None:
            target_sheet = self.closed_sheet
            
        # Calculate Total_Amount if it's for CLOSED sheet and not already present or needs override
        total_amount = lead_data.get("Total_Amount", "")
        if new_status == "CLOSED":
            try:
                price = float(str(lead_data.get("Price_Shown", 0)).replace(",", ""))
                qty = float(str(lead_data.get("Quantity_Asked", 0)).replace(",", ""))
                total_amount = str(round(price * qty, 2))
            except:
                pass

        target_row = [
            lead_data.get("Lead_ID"),
            lead_data.get("Customer_Name"),
            lead_data.get("Phone"),
            lead_data.get("Customer_Message"),
            lead_data.get("Product_ID"),
            lead_data.get("Product_Name"),
            lead_data.get("Quantity_Asked") if "Quantity_Asked" in lead_data else lead_data.get("Brand", ""), # Handling varying schemas if any
            lead_data.get("Price_Shown"),
            total_amount,
            lead_data.get("Lead_Date"),
            lead_data.get("Lead_Time"),
            new_status,
            datetime.now().strftime("%d-%m-%Y")
        ]
        
        target_sheet.append_row(target_row)
        source_sheet.delete_rows(row_index)
        logger.info(f"✅ Moved lead {lead_data.get('Lead_ID')} to {target_sheet.title}")

    def get_closed_leads(self) -> List[Dict]:
        """
        Get all leads from the closed sheet
        """
        try:
            return self.closed_sheet.get_all_records()
        except Exception as e:
            logger.error(f"❌ Error getting closed leads: {e}")
            return []
    
    def get_spreadsheet_url(self) -> str:
        """
        Get the public URL of the Google Sheet
        """
        try:
            return f"https://docs.google.com/spreadsheets/d/{self.sheet.id}"
        except Exception as e:
            logger.error(f"❌ Error getting spreadsheet ID: {e}")
            return "https://docs.google.com"

    def get_dashboard_stats(self) -> Dict:
        """
        Calculate dashboard statistics across all sheets with robust defaults
        """
        # Default stats structure to prevent frontend errors
        default_stats = {
            "total_leads": 0,
            "confirmed_count": 0,
            "active_count": 0,
            "cancelled_count": 0,
            "closed_count": 0,
            "total_revenue": 0,
            "total_products": 0,
            "hot_products": [],
            "conversion_rate": 0
        }
        
        try:
            # Aggregate all leads for counts - handle each sheet separately to be more resilient
            active_list = []
            try:
                active_list = self.leads_sheet.get_all_records()
            except Exception as e:
                logger.warning(f"⚠️ Error reading active leads: {e}")
                
            confirmed_list = []
            try:
                confirmed_list = self.confirmed_sheet.get_all_records()
            except Exception as e:
                logger.warning(f"⚠️ Error reading confirmed leads: {e}")
                
            closed_list = []
            try:
                closed_list = self.closed_sheet.get_all_records()
            except Exception as e:
                logger.warning(f"⚠️ Error reading closed leads: {e}")
            
            products = []
            try:
                products = self.get_products()
            except Exception as e:
                logger.warning(f"⚠️ Error reading products: {e}")
            
            # Calculate stats
            active_count = len([l for l in active_list if l.get("Status") == "ACTIVE"])
            confirmed_count = len([l for l in confirmed_list if l.get("Status") == "CONFIRMED"])
            cancelled_count = len([l for l in active_list if l.get("Status") == "CANCELLED"])
            closed_count = len(closed_list)
            
            total_all_leads = len(active_list) + len(confirmed_list) + len(closed_list)
            
            # Calculate revenue from CLOSED leads only (actual earnings)
            total_revenue = 0
            for lead in closed_list:
                try:
                    # Use the Total_Amount column directly if available and valid
                    total = lead.get("Total_Amount")
                    if total and str(total).strip():
                        total_revenue += float(str(total).replace(",", ""))
                    else:
                        # Fallback to calculation if column is missing or empty
                        price = float(str(lead.get("Price_Shown", 0)).replace(",", ""))
                        qty = float(str(lead.get("Quantity_Asked", 0)).replace(",", ""))
                        total_revenue += price * qty
                except:
                    pass
            
            # Find hot products (count across active and confirmed)
            product_counts = {}
            for lead in (active_list + confirmed_list):
                product = lead.get("Product_Name", "").strip()
                if product and product != "Unknown":
                    product_counts[product] = product_counts.get(product, 0) + 1
            
            hot_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Conversion rate 
            conversion_rate = round((closed_count / total_all_leads * 100) if total_all_leads > 0 else 0, 2)
            
            return {
                "total_leads": total_all_leads,
                "confirmed_count": confirmed_count,
                "active_count": active_count,
                "cancelled_count": cancelled_count,
                "closed_count": closed_count,
                "total_revenue": total_revenue,
                "total_products": len(products),
                "hot_products": [{"name": p[0], "count": p[1]} for p in hot_products],
                "conversion_rate": conversion_rate
            }
            
        except Exception as e:
            logger.error(f"❌ Critical error calculating stats: {e}", exc_info=True)
            return default_stats


# Global instance
_sheets_manager = None

def get_sheets_manager() -> SheetsManager:
    """Get or create the global SheetsManager instance"""
    global _sheets_manager
    if _sheets_manager is None:
        _sheets_manager = SheetsManager()
    return _sheets_manager
