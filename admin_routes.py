"""
Admin API Routes for AI Front Office Manager
Provides REST API endpoints for inventory and lead management
"""
from flask import Blueprint, jsonify, request
import logging
from datetime import datetime
from typing import Dict, List

from sheets_manager import get_sheets_manager

logger = logging.getLogger(__name__)

# Create Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api')

# Get sheets manager instance
sheets = get_sheets_manager()


# ==================== INVENTORY ENDPOINTS ====================

@admin_bp.route('/inventory', methods=['GET'])
def get_inventory():
    """Get all products from STOCK_MASTER"""
    try:
        products = sheets.get_products(use_cache=False)  # Fresh data
        return jsonify({
            'success': True,
            'data': products,
            'count': len(products)
        }), 200
    except Exception as e:
        logger.error(f"Error fetching inventory: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/inventory', methods=['POST'])
def add_product():
    """Add a new product to STOCK_MASTER"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['Product_Name', 'Brand', 'Base_Price']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        success = sheets.add_product(data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Product added successfully'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add product'
            }), 500
            
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/inventory/<product_name>', methods=['PUT'])
def update_product(product_name):
    """Update an existing product"""
    try:
        data = request.get_json()
        success = sheets.update_product(product_name, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Product updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Product not found or update failed'
            }), 404
            
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/inventory/<product_name>', methods=['DELETE'])
def delete_product(product_name):
    """Delete a product from STOCK_MASTER"""
    try:
        success = sheets.delete_product(product_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Product deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== LEAD MANAGEMENT ENDPOINTS ====================

@admin_bp.route('/leads', methods=['GET'])
def get_leads():
    """Get all leads with optional filtering"""
    try:
        status_filter = request.args.get('status', None)
        leads = sheets.get_all_leads(status_filter)
        
        return jsonify({
            'success': True,
            'data': leads,
            'count': len(leads)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/leads/closed', methods=['GET'])
def get_closed_leads():
    """Get all closed leads from CLOSED sheet"""
    try:
        closed_leads = sheets.get_closed_leads()
        
        return jsonify({
            'success': True,
            'data': closed_leads,
            'count': len(closed_leads)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching closed leads: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/leads/move-to-closed', methods=['POST'])
def move_lead_to_closed():
    """Move a confirmed lead to CLOSED sheet"""
    try:
        data = request.get_json()
        lead_id = data.get('lead_id')
        
        if not lead_id:
            return jsonify({
                'success': False,
                'error': 'lead_id is required'
            }), 400
        
        success = sheets.move_lead_to_closed(lead_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Lead moved to closed successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Lead not found or move failed'
            }), 404
            
    except Exception as e:
        logger.error(f"Error moving lead to closed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/leads/<lead_id>/status', methods=['PUT'])
def update_lead_status(lead_id):
    """Update lead status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({
                'success': False,
                'error': 'status is required'
            }), 400
        
        success = sheets.update_lead_status_by_id(lead_id, new_status)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Lead status updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Lead not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error updating lead status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/sheet-url', methods=['GET'])
def get_sheet_url():
    """Get the Google Sheet URL"""
    try:
        url = sheets.get_spreadsheet_url()
        return jsonify({
            'success': True,
            'url': url
        }), 200
    except Exception as e:
        logger.error(f"Error fetching sheet URL: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== ANALYTICS ENDPOINTS ====================

@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    try:
        stats = sheets.get_dashboard_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
