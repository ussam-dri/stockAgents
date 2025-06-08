from flask import Blueprint, jsonify, request
from datetime import datetime
from core.a2a_framework import A2ASystem
from database.oracle_connection import OracleConnection
from models import StockItem
from config.config import Config

api = Blueprint('api', __name__)

@api.route('/api/stock/current', methods=['GET'])
async def get_current_stock():
    try:
        db = OracleConnection(Config().oracle.__dict__)
        stock_items = await db.get_current_stock()
        return jsonify(stock_items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/stock/low', methods=['GET'])
async def get_low_stock():
    try:
        db = OracleConnection(Config().oracle.__dict__)
        low_stock_items = await db.get_low_stock_items()
        return jsonify(low_stock_items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/stock/<product_id>', methods=['PUT'])
async def update_stock(product_id):
    try:
        data = request.get_json()
        db = OracleConnection(Config().oracle.__dict__)
        
        if 'quantity' in data:
            await db.update_stock(product_id, data['quantity'])
            updated_item = await db.get_product_stock(product_id)
            return jsonify(updated_item)
        return jsonify({'error': 'Quantity is required'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/stock', methods=['POST'])
async def add_stock_item():
    try:
        data = request.get_json()
        required_fields = ['product_name', 'category', 'current_stock', 'unit']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        db = OracleConnection(Config().oracle.__dict__)
        
        # Create transaction record
        transaction = {
            'product_id': f"PROD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'transaction_type': 'ADD',
            'quantity': data['current_stock'],
            'unit_cost': data.get('unit_cost', 0),
            'total_cost': data.get('unit_cost', 0) * data['current_stock'],
            'supplier_id': data.get('supplier_id'),
            'reference_number': data.get('reference_number'),
            'notes': f"Initial stock addition for {data['product_name']}"
        }
        
        # Record the transaction
        await db.record_stock_transaction(transaction)
        
        # Get the updated stock information
        stock_info = await db.get_product_stock(transaction['product_id'])
        return jsonify(stock_info), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/stock/<product_id>', methods=['DELETE'])
async def delete_stock_item(product_id):
    try:
        db = OracleConnection(Config().oracle.__dict__)
        # In Oracle, we'll mark the item as inactive rather than deleting
        await db.execute_plsql_block(f"""
            UPDATE products 
            SET status = 'INACTIVE', 
                updated_date = SYSTIMESTAMP 
            WHERE product_id = '{product_id}'
        """)
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/system/status', methods=['GET'])
async def get_system_status():
    try:
        system = A2ASystem.get_instance()
        return jsonify({
            'total_agents': len(system.agents),
            'database_connected': system.database.is_connected(),
            'llm_enabled': system.llm is not None,
            'transport_type': system.transport.__class__.__name__
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500 