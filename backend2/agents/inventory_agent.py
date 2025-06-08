"""
Inventory Agent with Gemini LLM Integration
Monitors stock levels and triggers intelligent alerts
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import oracledb  # Changed from cx_Oracle to oracledb
from core.a2a_framework import A2AAgent, AgentAddress, MessageType
from core.gemini_integration import GeminiLLMService
from database.oracle_connection import OracleConnection
from config.config import Config

class InventoryAgent(A2AAgent):
    def __init__(self, config: Config, transport, llm_service: GeminiLLMService, db: OracleConnection):
        super().__init__("inventory_agent", transport)
        self.config = config
        self.db = db  # Use the provided db connection
        self.llm_service = llm_service
        self.check_interval = config.inventory.check_interval
        self.thresholds = config.inventory.thresholds
        self.capabilities = {
            'stock_monitoring': True,
            'threshold_alerts': True,
            'llm_enhanced_alerts': True
        }
        
        # Register message handlers
        self.register_handler('stock_query', self.handle_stock_query)
        self.register_handler('stock_update', self.handle_stock_update)
        self.register_handler('threshold_update', self.handle_threshold_update)
        
    async def start(self):
        """Start the inventory monitoring agent"""
        await super().start()
        await self.db.initialize()
        
        # Start periodic stock checking
        asyncio.create_task(self.monitor_stock_levels())
        self.logger.info("Inventory Agent started with LLM integration")
        
    async def monitor_stock_levels(self):
        """Continuously monitor stock levels with intelligent analysis"""
        while self.running:
            try:
                await self.check_stock_levels()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error monitoring stock: {e}")
                await asyncio.sleep(30)
                
    async def check_stock_levels(self):
        """Check current stock levels with LLM-enhanced analysis"""
        try:
            stock_data = await self.db.get_current_stock()
            low_stock_items = []
            
            for item in stock_data:
                product_id = item['product_id']
                current_stock = item['current_stock']
                threshold = self.thresholds.get(product_id, 50)
                
                if current_stock <= threshold:
                    # Determine urgency level
                    urgency = self._calculate_urgency(current_stock, threshold)
                    
                    # Get market conditions for LLM context
                    market_conditions = await self._get_market_conditions(product_id)
                    
                    # Generate intelligent alert message using LLM
                    alert_context = {
                        'product_name': item['product_name'],
                        'current_stock': current_stock,
                        'threshold': threshold,
                        'urgency': urgency,
                        'category': item.get('category', 'General'),
                        'market_conditions': market_conditions
                    }
                    
                    alert_message = await self.llm_service.generate_communication_message(
                        'stock_alert', alert_context
                    )
                    
                    low_stock_items.append({
                        **item,
                        'threshold': threshold,
                        'urgency': urgency,
                        'alert_message': alert_message,
                        'market_conditions': market_conditions
                    })
                    
                    await self.trigger_restock_event(item, urgency, market_conditions)
            
            if low_stock_items:
                self.logger.warning(f"Found {len(low_stock_items)} items below threshold")
                
        except Exception as e:
            self.logger.error(f"Error checking stock levels: {e}")
    
    def _calculate_urgency(self, current_stock: int, threshold: int) -> str:
        """Calculate urgency level based on stock ratio"""
        ratio = current_stock / threshold if threshold > 0 else 0
        
        if ratio <= 0.1:  # 10% or less of threshold
            return 'critical'
        elif ratio <= 0.3:  # 30% or less of threshold
            return 'high'
        elif ratio <= 0.6:  # 60% or less of threshold
            return 'medium'
        else:
            return 'low'
    
    async def _get_market_conditions(self, product_id: str) -> Dict:
        """Get current market conditions for the product"""
        # This would integrate with external market data APIs
        # For now, return mock data
        return {
            'demand': 'normal',
            'supply_chain': 'normal',
            'seasonal_factor': 1.0,
            'price_trend': 'stable',
            'availability': 'good'
        }
            
    async def trigger_restock_event(self, item: Dict, urgency: str, market_conditions: Dict):
        """Trigger intelligent restock event to supplier agents"""
        event_data = {
            'type': 'stock_alert',
            'product_id': item['product_id'],
            'product_name': item['product_name'],
            'current_stock': item['current_stock'],
            'threshold': self.thresholds.get(item['product_id'], 50),
            'urgency': urgency,
            'category': item.get('category', 'General'),
            'market_conditions': market_conditions,
            'timestamp': datetime.utcnow().isoformat(),
            'base_price': await self._get_base_price(item['product_id']),
            'min_quantity': max(50, item['current_stock'] * 2)  # Intelligent quantity calculation
        }
        
        # Broadcast to all supplier agents
        await self.broadcast_message(event_data, "supplier_alerts")
        
        # Notify stock manager
        stock_manager_address = AgentAddress("stock_manager_agent")
        await self.send_message(stock_manager_address, event_data, MessageType.NOTIFICATION)
        
        self.logger.info(f"Triggered intelligent restock event for {item['product_name']} (urgency: {urgency})")
        
    async def _get_base_price(self, product_id: str) -> float:
        """Get base price for product from database or external source"""
        # This would query historical pricing data
        base_prices = {
            'WIDGET_A': 10.50,
            'COMP_B': 2.75,
            'MAT_C': 1.25,
            'TOOL_D': 45.99
        }
        return base_prices.get(product_id, 100.0)
        
    async def handle_message(self, message):
        """Handle incoming messages"""
        content_type = message.content.get('type')
        
        if content_type == 'stock_query':
            await self.handle_stock_query(message)
        elif content_type == 'stock_update':
            await self.handle_stock_update(message)
        elif content_type == 'threshold_update':
            await self.handle_threshold_update(message)
        else:
            self.logger.warning(f"Unknown message type: {content_type}")
            
    async def handle_stock_query(self, message):
        """Handle stock level queries with LLM-enhanced responses"""
        product_id = message.content.get('product_id')
        
        if product_id:
            stock_info = await self.db.get_product_stock(product_id)
            if stock_info:
                # Enhance response with LLM analysis
                analysis_context = {
                    'product_name': stock_info['product_name'],
                    'current_stock': stock_info['current_stock'],
                    'threshold': self.thresholds.get(product_id, 50),
                    'trend': 'stable'  # Would calculate from historical data
                }
                
                analysis = await self.llm_service.generate_communication_message(
                    'stock_analysis', analysis_context
                )
                
                stock_info['llm_analysis'] = analysis
        else:
            stock_info = await self.db.get_current_stock()
            
        response_data = {
            'type': 'stock_response',
            'stock_data': stock_info,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.send_message(message.sender, response_data, MessageType.RESPONSE)
        
    async def handle_stock_update(self, message):
        """Handle stock level updates"""
        updates = message.content.get('updates', [])
        
        for update in updates:
            await self.db.update_stock(
                update['product_id'],
                update['quantity'],
                update['operation']
            )
            
        self.logger.info(f"Updated stock for {len(updates)} products")
        
        # Send confirmation
        response_data = {
            'type': 'update_confirmation',
            'updated_items': len(updates),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.send_message(message.sender, response_data, MessageType.RESPONSE)
        
    async def handle_threshold_update(self, message):
        """Handle threshold updates"""
        threshold_updates = message.content.get('thresholds', {})
        
        for product_id, new_threshold in threshold_updates.items():
            self.thresholds[product_id] = new_threshold
            
        self.logger.info(f"Updated thresholds for {len(threshold_updates)} products")
        
    async def get_inventory_status(self) -> Dict:
        """Get comprehensive inventory status with LLM insights"""
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
                urgency = self._calculate_urgency(stock_level, threshold)
                
                if urgency == 'critical':
                    status['critical_items'] += 1
                elif urgency in ['high', 'medium']:
                    status['low_stock_items'] += 1
                    
                status['items'].append({
                    **item,
                    'threshold': threshold,
                    'urgency': urgency,
                    'stock_ratio': stock_level / threshold if threshold > 0 else 0
                })
                
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting inventory status: {e}")
            return {'error': str(e)}