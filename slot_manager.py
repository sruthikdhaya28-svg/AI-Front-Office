"""
Slot Manager - Handles dynamic slot collection logic
Determines which fields are missing and what to ask next
"""
import logging
from typing import Dict, List, Optional, Any

from slot_config import get_required_slots, get_slot_config

logger = logging.getLogger(__name__)


def get_missing_required_slots(lead: Dict[str, Any]) -> List[Dict]:
    """
    Check which required fields are missing/empty in a lead
    
    Args:
        lead: Lead dictionary from Google Sheets
    
    Returns:
        List of slot configurations for missing fields, sorted by priority
    """
    required_slots = get_required_slots()
    missing = []
    
    for slot in required_slots:
        field_name = slot["field_name"]
        field_value = lead.get(field_name, "")
        
        # Consider empty string, None, or 0 as missing
        if not field_value or str(field_value).strip() == "":
            missing.append(slot)
            logger.debug(f"Missing slot: {field_name}")
    
    # Sort by priority (lower number = higher priority)
    missing.sort(key=lambda x: x["priority"])
    
    return missing


def get_next_slot_to_ask(lead: Dict[str, Any]) -> Optional[Dict]:
    """
    Determine the next slot to ask the customer for
    
    Args:
        lead: Lead dictionary from Google Sheets
    
    Returns:
        Slot configuration dict for the next field to ask, or None if all filled
    """
    missing_slots = get_missing_required_slots(lead)
    
    if missing_slots:
        next_slot = missing_slots[0]  # Highest priority
        logger.info(f"Next slot to ask: {next_slot['field_name']}")
        return next_slot
    
    logger.info("All required slots filled")
    return None


def generate_slot_question(slot_config: Dict) -> str:
    """
    Generate natural language question for a slot
    
    Args:
        slot_config: Slot configuration dictionary
    
    Returns:
        Question string to ask customer
    """
    return slot_config["question_template"]


def validate_slot_value(slot_config: Dict, value: Any) -> bool:
    """
    Validate a slot value against its validation rule
    
    Args:
        slot_config: Slot configuration dictionary
        value: Value to validate
    
    Returns:
        True if valid, False otherwise
    """
    validator = slot_config.get("validation")
    
    if validator is None:
        return True  # No validation required
    
    try:
        return validator(value)
    except Exception as e:
        logger.error(f"Validation error for {slot_config['field_name']}: {e}")
        return False


def extract_slot_from_ai_data(ai_data: Dict, slot_config: Dict) -> Optional[Any]:
    """
    Extract slot value from AI extraction result
    
    Args:
        ai_data: Dictionary from extract_structured_data()
        slot_config: Slot configuration
    
    Returns:
        Extracted value or None if not found
    """
    extraction_key = slot_config["ai_extraction_key"]
    value = ai_data.get(extraction_key)
    
    if value:
        logger.info(f"Extracted {slot_config['field_name']}: {value}")
    
    return value


def is_all_slots_filled(lead: Dict[str, Any]) -> bool:
    """
    Check if all required slots are filled
    
    Args:
        lead: Lead dictionary from Google Sheets
    
    Returns:
        True if all required fields are filled, False otherwise
    """
    missing = get_missing_required_slots(lead)
    return len(missing) == 0


def get_slot_summary(lead: Dict[str, Any]) -> str:
    """
    Generate a summary of filled slots for confirmation message
    
    Args:
        lead: Lead dictionary from Google Sheets
    
    Returns:
        Human-readable summary string
    """
    required_slots = get_required_slots()
    summary_parts = []
    
    for slot in sorted(required_slots, key=lambda x: x["priority"]):
        field_name = slot["field_name"]
        value = lead.get(field_name, "")
        
        if value:
            display_name = slot["display_name"].capitalize()
            summary_parts.append(f"{display_name}: {value}")
    
    return ", ".join(summary_parts)
