import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import cx_Oracle
try:
    from google.adk import Agent
    from google.adk.events import Message
except ModuleNotFoundError:
    import sys
    sys.stderr.write(
        "ERROR: google-adk module not found or incorrect import path. "
        "Ensure 'google-adk' is installed via 'pip install google-adk' and check the correct import path in documentation.\n"
    )
    raise

# Temporary fallback for AgentAddress until correct import is found
# TODO: Replace with actual import (e.g., from google.adk.<submodule> import AgentAddress) after checking documentation or submodule contents
class AgentAddress:
    def __init__(self, group: str, host: str, port: int = 8001):
        self.group = group
        self.host = host
        self.port = port

from ..database.oracle_connection import OracleConnection
from ..config.config import Config

class InventoryAgent(Agent):
    def __init__(self, config: Config):
        super().__init__(
            name="InventoryAgent",
            address=AgentAddress("inventory", "localhost", 8001)
        )
        self.config = config
        self.db = OracleConnection(config.oracle)
        self.check_interval = config.inventory.check_interval
        self.thresholds = config.inventory.thresholds
        self.logger = logging.getLogger(__name__)
        
    async def start(self):
        """Start the inventory monitoring agent"""
        self.logger.info("Inventory Agent starting...")
        await self.register()
        
        # Start periodic stock checking
        asyncio.create_task(self.monitor_stock_levels())
        
    async def monitor_stock_levels(self):
        """Continuously monitor stock levels"""
        while True:
            try:
                await self.check_stock_levels()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error monitoring stock: {e}")
                await asyncio.sleep(30)  # Wait before retrying
                
    async def check_stock_levels(self):
        """Check current stock levels against thresholds"""
        try:
            stock_data = await self.db.get_current_stock()
            
            for item in stock_data:
                product_id = item['product_id']
                current_stock = item['current_stock']
                threshold = self.thresholds.get(product_id, 50)  # Default threshold
                
                if current_stock <= threshold:
                    await self.trigger_restock_event(item)
                    
        except Exception as e:
            self.logger.error(f"Error checking stock levels: {e}")
            
    async def trigger_restock_event(self, item: Dict):
        """Trigger out-of-stock event to supplier agents"""
        event_data = {
            'event_type': 'stock_low',
            'product_id': item['product_id'],
            'product_name': item['product_name'],
            'current_stock': item['current_stock'],
            'threshold': self.thresholds.get(item['product_id'], 50),
            'timestamp': datetime.utcnow().isoformat(),
            'urgency': 'high' if item['current_stock'] == 0 else 'medium'
        }
        
        # Broadcast to all supplier agents
        message = Message(
            sender=self.address,
            recipient=AgentAddress("broadcast", "suppliers"),
            content=event_data,
            message_type="stock_alert"
        )
        
        await self.send_message(message)
        self.logger.info(f"Triggered restock event for {item['product_name']}")
        
    async def handle_message(self, message: Message):
        """Handle incoming messages"""
        if message.message_type == "stock_query":
            await self.handle_stock_query(message)
        elif message.message_type == "stock_update":
            await self.handle_stock_update(message)
            
    async def handle_stock_query(self, message: Message):
        """Handle stock level queries"""
        product_id = message.content.get('product_id')
        
        if product_id:
            stock_info = await self.db.get_product_stock(product_id)
        else:
            stock_info = await self.db.get_current_stock()
            
        response = Message(
            sender=self.address,
            recipient=message.sender,
            content={'stock_data': stock_info},
            message_type="stock_response"
        )
        
        await self.send_message(response)
        
    async def handle_stock_update(self, message: Message):
        """Handle stock level updates"""
        updates = message.content.get('updates', [])
        
        for update in updates:
            await self.db.update_stock(
                update['product_id'],
                update['quantity'],
                update['operation']  # 'add' or 'subtract'
            )
            
        self.logger.info(f"Updated stock for {len(updates)} products")
        
    async def get_inventory_status(self) -> Dict:
        """Get current inventory status for dashboard"""
        try:
            stock_data = await self.db.get_current_stock()
            
            status = {
                'total_products': len(stock_data),
                'low_stock_items': 0,
                'critical_items': 0,
                'last_check': datetime.utcnow().isoformat(),
                'items': []
            }
            
            for item in stock_data:
                threshold = self.thresholds.get(item['product_id'], 50)
                stock_level = item['current_stock']
                
                if stock_level == 0:
                    status['critical_items'] += 1
                elif stock_level <= threshold:
                    status['low_stock_items'] += 1
                    
                status['items'].append({
                    **item,
                    'threshold': threshold,
                    'status': 'critical' if stock_level == 0 else 
                             'low' if stock_level <= threshold else 'normal'
                })
                
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting inventory status: {e}")
            return {'error': str(e)}