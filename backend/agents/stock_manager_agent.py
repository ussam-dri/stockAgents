"""
Stock Manager Agent - Collects offers and selects the best one
Coordinates between suppliers and manager approval
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from google_adk import Agent, Message, AgentAddress
from ..config.config import Config
from ..notifications.email_service import EmailService

class StockManagerAgent(Agent):
    def __init__(self, config: Config):
        super().__init__(
            name="StockManagerAgent",
            address=AgentAddress("stock_manager", "localhost", 8005)
        )
        self.config = config
        self.email_service = EmailService(config.email)
        self.active_requests = {}  # Track active restock requests
        self.offer_timeout = config.stock_manager.offer_timeout
        self.selection_criteria = config.stock_manager.selection_criteria
        self.logger = logging.getLogger(__name__)
        
    async def start(self):
        """Start the stock manager agent"""
        self.logger.info("Stock Manager Agent starting...")
        await self.register()
        
    async def handle_message(self, message: Message):
        """Handle incoming messages"""
        if message.message_type == "supplier_offer":
            await self.handle_supplier_offer(message)
        elif message.message_type == "manager_approval":
            await self.handle_manager_approval(message)
        elif message.message_type == "offer_timeout":
            await self.handle_offer_timeout(message)
            
    async def handle_supplier_offer(self, message: Message):
        """Handle offer from supplier agent"""
        offer = message.content
        product_id = offer['product_id']
        
        # Initialize request tracking if first offer
        if product_id not in self.active_requests:
            self.active_requests[product_id] = {
                'product_id': product_id,
                'product_name': offer['product_name'],
                'offers': [],
                'start_time': datetime.utcnow(),
                'status': 'collecting_offers'
            }
            
            # Set timeout for offer collection
            asyncio.create_task(
                self.set_offer_timeout(product_id, self.offer_timeout)
            )
            
        # Add offer to collection
        self.active_requests[product_id]['offers'].append(offer)
        self.logger.info(f"Received offer from {offer['supplier_name']} for {offer['product_name']}")
        
        # Check if we have enough offers or timeout reached
        if len(self.active_requests[product_id]['offers']) >= 3:
            await self.evaluate_offers(product_id)
            
    async def set_offer_timeout(self, product_id: str, timeout_seconds: int):
        """Set timeout for offer collection"""
        await asyncio.sleep(timeout_seconds)
        
        if product_id in self.active_requests and self.active_requests[product_id]['status'] == 'collecting_offers':
            await self.evaluate_offers(product_id)
            
    async def evaluate_offers(self, product_id: str):
        """Evaluate collected offers and select the best one"""
        if product_id not in self.active_requests:
            return
            
        request = self.active_requests[product_id]
        offers = request['offers']
        
        if not offers:
            self.logger.warning(f"No offers received for {product_id}")
            return
            
        # Select best offer based on criteria
        best_offer = await self.select_best_offer(offers)
        
        if best_offer:
            request['selected_offer'] = best_offer
            request['status'] = 'awaiting_approval'
            
            # Send for manager approval
            await self.request_manager_approval(product_id, best_offer)
        else:
            self.logger.error(f"Failed to select offer for {product_id}")
            
    async def select_best_offer(self, offers: List[Dict]) -> Optional[Dict]:
        """Select the best offer based on configured criteria"""
        if not offers:
            return None
            
        # Score each offer
        scored_offers = []
        
        for offer in offers:
            score = 0
            
            # Price scoring (lower is better)
            if self.selection_criteria.get('price_weight', 0.4) > 0:
                price_scores = [o['total_price'] for o in offers]
                min_price = min(price_scores)
                max_price = max(price_scores)
                
                if max_price > min_price:
                    price_score = (max_price - offer['total_price']) / (max_price - min_price)
                else:
                    price_score = 1.0
                    
                score += price_score * self.selection_criteria.get('price_weight', 0.4)
                
            # Delivery time scoring (faster is better)
            if self.selection_criteria.get('speed_weight', 0.3) > 0:
                delivery_scores = [o['delivery_days'] for o in offers]
                min_delivery = min(delivery_scores)
                max_delivery = max(delivery_scores)
                
                if max_delivery > min_delivery:
                    speed_score = (max_delivery - offer['delivery_days']) / (max_delivery - min_delivery)
                else:
                    speed_score = 1.0
                    
                score += speed_score * self.selection_criteria.get('speed_weight', 0.3)
                
            # Supplier reliability scoring (mock)
            reliability_score = self.get_supplier_reliability(offer['supplier_id'])
            score += reliability_score * self.selection_criteria.get('reliability_weight', 0.3)
            
            scored_offers.append((score, offer))
            
        # Select highest scoring offer
        scored_offers.sort(key=lambda x: x[0], reverse=True)
        best_offer = scored_offers[0][1]
        
        self.logger.info(f"Selected offer from {best_offer['supplier_name']} - ${best_offer['total_price']}")
        return best_offer
        
    def get_supplier_reliability(self, supplier_id: str) -> float:
        """Get supplier reliability score (mock implementation)"""
        # This would integrate with historical data
        reliability_scores = {
            '1': 0.9,  # Supplier Alpha - high reliability
            '2': 0.8,  # Supplier Beta - good reliability
            '3': 0.7   # Supplier Gamma - average reliability
        }
        return reliability_scores.get(supplier_id, 0.5)
        
    async def request_manager_approval(self, product_id: str, offer: Dict):
        """Send approval request to manager"""
        request = self.active_requests[product_id]
        
        # Prepare approval data
        approval_data = {
            'request_id': f"REQ_{product_id}_{int(datetime.utcnow().timestamp())}",
            'product_id': product_id,
            'product_name': offer['product_name'],
            'selected_offer': offer,
            'alternatives': len(request['offers']) - 1,
            'urgency': offer.get('urgency', 'medium'),
            'total_cost': offer['total_price'],
            'delivery_date': offer['delivery_date']
        }
        
        # Send email notification
        await self.email_service.send_approval_request(approval_data)
        
        # Send message to manager agent
        message = Message(
            sender=self.address,
            recipient=AgentAddress("manager", "localhost", 8006),
            content=approval_data,
            message_type="approval_request"
        )
        
        await self.send_message(message)
        self.logger.info(f"Sent approval request for {offer['product_name']}")
        
    async def handle_manager_approval(self, message: Message):
        """Handle manager approval/rejection"""
        approval_data = message.content
        request_id = approval_data['request_id']
        decision = approval_data['decision']  # 'approved' or 'rejected'
        
        # Find the request
        product_id = None
        for pid, request in self.active_requests.items():
            if request.get('selected_offer', {}).get('request_id') == request_id:
                product_id = pid
                break
                
        if not product_id:
            self.logger.error(f"Request {request_id} not found")
            return
            
        request = self.active_requests[product_id]
        
        if decision == 'approved':
            await self.process_approved_order(product_id, request['selected_offer'])
        else:
            await self.handle_rejected_order(product_id, approval_data.get('reason', 'No reason provided'))
            
        # Clean up request
        del self.active_requests[product_id]
        
    async def process_approved_order(self, product_id: str, offer: Dict):
        """Process approved order"""
        # Send order confirmation to supplier
        order_message = Message(
            sender=self.address,
            recipient=AgentAddress(f"supplier_{offer['supplier_id']}", "localhost", 8002 + int(offer['supplier_id'])),
            content=offer,
            message_type="order_confirmation"
        )
        
        await self.send_message(order_message)
        
        # Notify inventory agent of incoming stock
        inventory_message = Message(
            sender=self.address,
            recipient=AgentAddress("inventory", "localhost", 8001),
            content={
                'product_id': product_id,
                'quantity': offer['quantity'],
                'expected_date': offer['delivery_date'],
                'supplier': offer['supplier_name']
            },
            message_type="incoming_stock"
        )
        
        await self.send_message(inventory_message)
        
        self.logger.info(f"Order processed for {offer['product_name']}")
        
    async def handle_rejected_order(self, product_id: str, reason: str):
        """Handle rejected order"""
        self.logger.info(f"Order rejected for {product_id}: {reason}")
        
        # Could implement alternative logic here (e.g., select next best offer)
        
    async def get_manager_status(self) -> Dict:
        """Get current stock manager status"""
        return {
            'active_requests': len(self.active_requests),
            'requests': list(self.active_requests.keys()),
            'last_activity': datetime.utcnow().isoformat(),
            'status': 'active'
        }