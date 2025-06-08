"""
Supplier Agent with Gemini LLM Integration
Generates intelligent offers using LLM
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Optional
from core.a2a_framework import A2AAgent, AgentAddress, MessageType
from core.gemini_integration import GeminiLLMService
from config.config import Config

class SupplierAgent(A2AAgent):
    def __init__(self, supplier_id: str, supplier_name: str, config: Config, 
                 transport, llm_service: GeminiLLMService):
        super().__init__(f"supplier_agent_{supplier_id}", transport)
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.config = config
        self.llm_service = llm_service
        
        # Get supplier configuration
        supplier_config = config.suppliers.get(supplier_id, {})
        self.catalog = supplier_config.catalog
        self.pricing_strategy = supplier_config.pricing_strategy
        self.location = supplier_config.location
        
        self.capabilities = {
            'offer_generation': True,
            'llm_pricing': True,
            'market_analysis': True,
            'competitive_bidding': True
        }
        
        # Supplier profile for LLM
        self.supplier_profile = {
            'id': supplier_id,
            'name': supplier_name,
            'location': self.location,
            'pricing_strategy': self.pricing_strategy,
            'reliability': self._get_reliability_score(),
            'specialties': self._get_specialties()
        }
        
        # Register message handlers
        self.register_handler('stock_alert', self.handle_stock_alert)
        self.register_handler('offer_request', self.handle_offer_request)
        self.register_handler('order_confirmation', self.handle_order_confirmation)
        
    async def start(self):
        """Start the supplier agent"""
        await super().start()
        
        # Subscribe to supplier alerts
        await self.transport.subscribe("supplier_alerts", self._handle_broadcast_alert)
        
        self.logger.info(f"Supplier Agent {self.supplier_name} started with LLM integration")
        
    def _get_reliability_score(self) -> float:
        """Get supplier reliability score"""
        reliability_scores = {
            '1': 0.9,  # Supplier Alpha - high reliability
            '2': 0.8,  # Supplier Beta - good reliability
            '3': 0.7   # Supplier Gamma - average reliability
        }
        return reliability_scores.get(self.supplier_id, 0.5)
    
    def _get_specialties(self) -> list:
        """Get supplier specialties"""
        specialties_map = {
            '1': ['electronics', 'fast_delivery', 'bulk_orders'],
            '2': ['premium_quality', 'european_standards', 'small_batches'],
            '3': ['cost_effective', 'large_volumes', 'flexible_terms']
        }
        return specialties_map.get(self.supplier_id, ['general'])
        
    async def _handle_broadcast_alert(self, message):
        """Handle broadcast stock alerts"""
        if message.content.get('type') == 'stock_alert':
            await self.handle_stock_alert(message)
        
    async def handle_message(self, message):
        """Handle incoming messages"""
        content_type = message.content.get('type')
        
        if content_type == 'stock_alert':
            await self.handle_stock_alert(message)
        elif content_type == 'offer_request':
            await self.handle_offer_request(message)
        elif content_type == 'order_confirmation':
            await self.handle_order_confirmation(message)
        else:
            self.logger.warning(f"Unknown message type: {content_type}")
            
    async def handle_stock_alert(self, message):
        """Handle stock alert with LLM-generated offer"""
        alert_data = message.content
        product_id = alert_data.get('product_id')
        
        # Check if we can supply this product
        if product_id in self.catalog:
            # Prepare product information for LLM
            product_info = {
                'id': product_id,
                'name': alert_data.get('product_name'),
                'current_stock': alert_data.get('current_stock'),
                'threshold': alert_data.get('threshold'),
                'category': alert_data.get('category'),
                'urgency': alert_data.get('urgency', 'medium'),
                'base_price': alert_data.get('base_price', self.catalog[product_id]['base_price']),
                'min_quantity': alert_data.get('min_quantity', self.catalog[product_id].get('min_order_quantity', 50))
            }
            
            # Get market conditions
            market_conditions = alert_data.get('market_conditions', {})
            
            # Generate intelligent offer using LLM
            offer = await self.llm_service.generate_supplier_offer(
                product_info, self.supplier_profile, market_conditions
            )
            
            if offer:
                # Add additional metadata
                offer.update({
                    'offer_id': f"{self.supplier_id}_{product_id}_{int(datetime.utcnow().timestamp())}",
                    'product_id': product_id,
                    'product_name': product_info['name'],
                    'delivery_date': (datetime.utcnow() + timedelta(days=offer['delivery_days'])).isoformat(),
                    'terms': self.catalog[product_id].get('terms', 'Standard terms'),
                    'timestamp': datetime.utcnow().isoformat(),
                    'urgency': product_info['urgency']
                })
                
                # Send offer to stock manager
                stock_manager_address = AgentAddress("stock_manager_agent")
                offer_message = {
                    'type': 'supplier_offer',
                    'offer': offer
                }
                
                await self.send_message(stock_manager_address, offer_message, MessageType.REQUEST)
                
                self.logger.info(f"Sent LLM-generated offer for {product_info['name']}: ${offer['total_price']}")
            else:
                self.logger.warning(f"Failed to generate offer for {product_info['name']}")
                
    async def handle_offer_request(self, message):
        """Handle direct offer requests"""
        request_data = message.content
        product_id = request_data.get('product_id')
        quantity = request_data.get('quantity')
        
        if product_id in self.catalog:
            # Generate custom offer for specific quantity
            product_info = {
                'id': product_id,
                'name': request_data.get('product_name', f'Product {product_id}'),
                'base_price': self.catalog[product_id]['base_price'],
                'min_quantity': quantity,
                'urgency': request_data.get('urgency', 'medium')
            }
            
            market_conditions = request_data.get('market_conditions', {})
            
            offer = await self.llm_service.generate_supplier_offer(
                product_info, self.supplier_profile, market_conditions
            )
            
            if offer:
                offer.update({
                    'offer_id': f"{self.supplier_id}_{product_id}_{int(datetime.utcnow().timestamp())}",
                    'product_id': product_id,
                    'delivery_date': (datetime.utcnow() + timedelta(days=offer['delivery_days'])).isoformat(),
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                response_data = {
                    'type': 'offer_response',
                    'offer': offer
                }
                
                await self.send_message(message.sender, response_data, MessageType.RESPONSE)
                
    async def handle_order_confirmation(self, message):
        """Handle order confirmation from manager"""
        order_data = message.content.get('order', {})
        
        # Process the order with LLM-generated confirmation
        confirmation_context = {
            'order_id': order_data.get('offer_id'),
            'product_name': order_data.get('product_name'),
            'quantity': order_data.get('quantity'),
            'total_price': order_data.get('total_price'),
            'delivery_date': order_data.get('delivery_date'),
            'supplier_name': self.supplier_name
        }
        
        confirmation_message = await self.llm_service.generate_communication_message(
            'order_confirmation', confirmation_context
        )
        
        self.logger.info(f"Order confirmed: {order_data.get('offer_id')}")
        
        # Simulate order processing
        await self.process_order(order_data)
        
        # Send confirmation back
        confirmation_data = {
            'type': 'order_processed',
            'order_id': order_data.get('offer_id'),
            'status': 'confirmed',
            'estimated_delivery': order_data.get('delivery_date'),
            'tracking_number': f"TRK{random.randint(100000, 999999)}",
            'confirmation_message': confirmation_message,
            'supplier_contact': f"{self.supplier_name} Customer Service"
        }
        
        await self.send_message(message.sender, confirmation_data, MessageType.RESPONSE)
        
    async def process_order(self, order_data: Dict):
        """Process the order (enhanced with LLM insights)"""
        # This would integrate with actual supplier systems
        await asyncio.sleep(1)  # Simulate processing time
        
        # Log processing details
        self.logger.info(f"Processing order {order_data.get('offer_id')} for {order_data.get('quantity')} units")
        
        # Could use LLM to generate processing updates, shipping notifications, etc.
        
    async def get_supplier_status(self) -> Dict:
        """Get current supplier status with LLM insights"""
        return {
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'location': self.location,
            'status': self.state,
            'products_available': len(self.catalog),
            'pricing_strategy': self.pricing_strategy,
            'reliability_score': self.supplier_profile['reliability'],
            'specialties': self.supplier_profile['specialties'],
            'llm_enabled': True,
            'last_activity': datetime.utcnow().isoformat()
        }