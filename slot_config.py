"""
Slot Configuration for Schema-Driven Conversation Flow
Defines which fields to ask from customers and how to ask them
"""

# Slot categories define how the system handles each field
SLOT_CATEGORIES = {
    # Fields that MUST be collected from customer through conversation
    "REQUIRED_FROM_CUSTOMER": [
        {
            "field_name": "Product_Name",
            "display_name": "product",
            "question_template": "Which product do you need?",
            "ai_extraction_key": "product_detected",
            "priority": 1,  # Ask first
            "validation": None  # Optional: validation function
        },
        {
            "field_name": "Quantity_Asked",
            "display_name": "quantity",
            "question_template": "How many quantity do you need?",
            "ai_extraction_key": "quantity_detected",
            "priority": 2,  # Ask second
            "validation": lambda x: str(x).isdigit() and int(x) > 0
        },
        # ADD MORE FIELDS HERE:
        # Example for future:
        # {
        #     "field_name": "Color",
        #     "display_name": "color",
        #     "question_template": "Which color do you need?",
        #     "ai_extraction_key": "color_detected",
        #     "priority": 3,
        #     "validation": None
        # },
    ],
    
    # Fields that can be extracted from conversation but not explicitly asked
    "OPTIONAL_FROM_CUSTOMER": [
        "Brand",  # Extract if customer mentions brand preference
        "Customer_Name",  # Extract from message if they introduce themselves
    ],
    
    # Fields managed by the system - never ask customer
    "SYSTEM_MANAGED": [
        "Lead_ID",
        "Lead_Date",
        "Lead_Time",
        "Status",
        "Last_Action_Date",
        "Last_Reminder_Date",
        "No.of_Reminders_Pending",
        "Product_ID",
        "Price_Shown",
        "Customer_Message",
    ]
}


def get_required_slots():
    """Get list of all required slot configurations"""
    return SLOT_CATEGORIES["REQUIRED_FROM_CUSTOMER"]


def get_optional_slots():
    """Get list of all optional slot field names"""
    return SLOT_CATEGORIES["OPTIONAL_FROM_CUSTOMER"]


def get_system_slots():
    """Get list of all system-managed field names"""
    return SLOT_CATEGORIES["SYSTEM_MANAGED"]


def get_slot_config(field_name: str):
    """
    Get configuration for a specific field
    
    Args:
        field_name: Name of the field (e.g., "Product_Name")
    
    Returns:
        Slot configuration dict or None if not found
    """
    for slot in get_required_slots():
        if slot["field_name"] == field_name:
            return slot
    return None


def is_required_slot(field_name: str) -> bool:
    """Check if a field is required from customer"""
    return any(slot["field_name"] == field_name for slot in get_required_slots())


def is_optional_slot(field_name: str) -> bool:
    """Check if a field is optional from customer"""
    return field_name in get_optional_slots()


def is_system_slot(field_name: str) -> bool:
    """Check if a field is system-managed"""
    return field_name in get_system_slots()
