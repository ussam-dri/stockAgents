"""
Supplier Agent - Listens for stock alerts and provides offers
Multiple instances can run representing different suppliers
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Optional
from google_adk import Agent, Message, AgentAddress
from ..config.config import Config

class SupplierAgent(Agent):
    def __init__(self, supplier_id: str, supplier_name: str, config: Config):
        super().__init__(
            name=f"SupplierAgent_{supplier_id}",
            address=AgentAddress(f"supplier_{supplier_id}", "localhost", 8002 + int(supplier_id))
        )
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.config = config
        self.catalog = config.suppliers[supplier_id].catalog
        self.pricing_strategy = config.suppliers[supplier_id].pricing_strategy
        self.location = config.suppliers[supplier_id].location
        self.logger = logging.getLogger(f"{__name__}.{supplier_id}")
        
    async def start(self):
        """Start the supplier agent"""
        self.logger.info(f"Supplier Agent {self.supplier_name} starting...")
        await self.register()
        
        # Subscribe to stock alerts
        await self.subscribe_to_events("stock_alert")
        
    async def handle_message(self, message: Message):
        """Handle incoming messages"""
        if message.message_type == "stock_alert":
            await self.handle_stock_alert(message)
        elif message.message_type == "offer_request":
            await self.handle_offer_request(message)
        elif message.message_type == "order_confirmation":
            await self.handle_order_confirmation(message)
            
    async def handle_stock_alert(self, message: Message):
        """Handle stock alert from inventory agent"""
        product_id = message.content.get('product_id')
        product_name = message.content.get('product_name')
        urgency = message.content.get('urgency', 'medium')
        
        # Check if we can supply this product
        if product_id in self.catalog:
            offer = await self.generate_offer(product_id, product_name, urgency)
            
            if offer:
                # Send offer to stock manager
                offer_message = Message(
                    sender=self.address,
                    recipient=AgentAddress("stock_manager", "localhost", 8005),
                    content=offer,
                    message_type="supplier_offer"
                )
                
                await self.send_message(offer_message)
                self.logger.info(f"Sent offer for {product_name}: ${offer['price']}")
                
    async def generate_offer(self, product_id: str, product_name: str, urgency: str) -> Optional[Dict]:
        """Generate offer based on product and pricing strategy"""
        try:
            product_info = self.catalog[product_id]
            base_price = product_info['base_price']
            
            # Apply pricing strategy
            if self.pricing_strategy == 'competitive':
                # Lower prices but longer delivery
                price_multiplier = random.uniform(0.85, 1.1)
                delivery_days = random.randint(3, 7)
            elif self.pricing_strategy == 'premium':
                # Higher prices but faster delivery
                price_multiplier = random.uniform(1.1, 1.3)
                delivery_days = random.randint(1, 3)
            else:  # 'standard'
                price_multiplier = random.uniform(0.95, 1.15)
                delivery_days = random.randint(2, 5)
                
            # Adjust for urgency
            if urgency == 'high':
                price_multiplier *= 1.2  # Emergency surcharge
                delivery_days = max(1, delivery_days - 1)
                
            # Calculate final offer
            quantity = product_info.get('min_order_quantity', 50)
            unit_price = base_price * price_multiplier
            total_price = unit_price * quantity
            
            offer = {
                'offer_id': f"{self.supplier_id}_{product_id}_{int(datetime.utcnow().timestamp())}",
                'supplier_id': self.supplier_id,
                'supplier_name': self.supplier_name,
                'product_id': product_id,
                'product_name': product_name,
                'quantity': quantity,
                'unit_price': round(unit_price, 2),
                'total_price': round(total_price, 2),
                'delivery_days': delivery_days,
                'delivery_date': (datetime.utcnow() + timedelta(days=delivery_days)).isoformat(),
                'location': self.location,
                'terms': product_info.get('terms', 'Standard terms'),
                'timestamp': datetime.utcnow().isoformat(),
                'urgency': urgency
            }
            
            return offer
            
        except Exception as e:
            self.logger.error(f"Error generating offer: {e}")
            return None
            
    async def handle_offer_request(self, message: Message):
        """Handle direct offer requests"""
        product_id = message.content.get('product_id')
        quantity = message.content.get('quantity')
        
        if product_id in self.catalog:
            # Generate custom offer based on requested quantity
            offer = await self.generate_custom_offer(product_id, quantity)
            
            response = Message(
                sender=self.address,
                recipient=message.sender,
                content=offer,
                message_type="offer_response"
            )
            
            await self.send_message(response)
            
    async def generate_custom_offer(self, product_id: str, quantity: int) -> Dict:
        """Generate custom offer for specific quantity"""
        product_info = self.catalog[product_id]
        base_price = product_info['base_price']
        
        # Volume discounts
        if quantity >= 100:
            price_multiplier = 0.9
        elif quantity >= 50:
            price_multiplier = 0.95
        else:
            price_multiplier = 1.0
            
        unit_price = base_price * price_multiplier
        total_price = unit_price * quantity
        
        # Delivery time based on quantity
        delivery_days = max(1, min(7, quantity // 20))
        
        return {
            'offer_id': f"{self.supplier_id}_{product_id}_{int(datetime.utcnow().timestamp())}",
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': round(unit_price, 2),
            'total_price': round(total_price, 2),
            'delivery_days': delivery_days,
            'delivery_date': (datetime.utcnow() + timedelta(days=delivery_days)).isoformat(),
            'location': self.location,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    async def handle_order_confirmation(self, message: Message):
        """Handle order confirmation from manager"""
        order_data = message.content
        
        # Process the order
        self.logger.info(f"Order confirmed: {order_data['offer_id']}")
        
        # Update internal systems (mock)
        await self.process_order(order_data)
        
        # Send confirmation back
        confirmation = Message(
            sender=self.address,
            recipient=message.sender,
            content={
                'order_id': order_data['offer_id'],
                'status': 'confirmed',
                'estimated_delivery': order_data['delivery_date'],
                'tracking_number': f"TRK{random.randint(100000, 999999)}"
            },
            message_type="order_processed"
        )
        
        await self.send_message(confirmation)
        
    async def process_order(self, order_data: Dict):
        """Process the order (mock implementation)"""
        # This would integrate with actual supplier systems
        await asyncio.sleep(1)  # Simulate processing time
        self.logger.info(f"Processing order {order_data['offer_id']}")
        
    async def get_supplier_status(self) -> Dict:
        """Get current supplier status"""
        return {
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'location': self.location,
            'status': 'active',
            'products_available': len(self.catalog),
            'pricing_strategy': self.pricing_strategy,
            'last_activity': datetime.utcnow().isoformat()
        }