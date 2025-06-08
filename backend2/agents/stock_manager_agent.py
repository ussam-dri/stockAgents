"""
Stock Manager Agent with Gemini LLM Integration
Uses LLM for intelligent offer evaluation and selection
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from core.a2a_framework import A2AAgent, AgentAddress, MessageType
from core.gemini_integration import GeminiLLMService
from config.config import Config

class StockManagerAgent(A2AAgent):
    def __init__(self, config: Config, transport, llm_service: GeminiLLMService):
        super().__init__("stock_manager_agent", transport)
        self.config = config
        self.llm_service = llm_service
        self.active_requests = {}  # Track active restock requests
        self.offer_timeout = config.stock_manager.offer_timeout
        self.selection_criteria = config.stock_manager.selection_criteria
        
        self.capabilities = {
            'offer_evaluation': True,
            'llm_analysis': True,
            'intelligent_selection': True,
            'risk_assessment': True
        }
        
        # Register message handlers
        self.register_handler('supplier_offer', self.handle_supplier_offer)
        self.register_handler('manager_approval', self.handle_manager_approval)
        self.register_handler('stock_alert', self.handle_stock_alert)
        
    async def start(self):
        """Start the stock manager agent"""
        await super().start()
        self.logger.info("Stock Manager Agent started with LLM integration")
        
    async def handle_message(self, message):
        """Handle incoming messages"""
        content_type = message.content.get('type')
        
        if content_type == 'supplier_offer':
            await self.handle_supplier_offer(message)
        elif content_type == 'manager_approval':
            await self.handle_manager_approval(message)
        elif content_type == 'stock_alert':
            await self.handle_stock_alert(message)
        else:
            self.logger.warning(f"Unknown message type: {content_type}")
            
    async def handle_stock_alert(self, message):
        """Handle stock alert and initialize request tracking"""
        alert_data = message.content
        product_id = alert_data.get('product_id')
        
        if product_id not in self.active_requests:
            self.active_requests[product_id] = {
                'product_id': product_id,
                'product_name': alert_data.get('product_name'),
                'alert_data': alert_data,
                'offers': [],
                'start_time': datetime.utcnow(),
                'status': 'collecting_offers'
            }
            
            # Set timeout for offer collection
            asyncio.create_task(
                self.set_offer_timeout(product_id, self.offer_timeout)
            )
            
            self.logger.info(f"Started collecting offers for {alert_data.get('product_name')}")
            
    async def handle_supplier_offer(self, message):
        """Handle offer from supplier agent with LLM validation"""
        offer_data = message.content.get('offer', {})
        product_id = offer_data.get('product_id')
        
        if not product_id:
            self.logger.warning("Received offer without product_id")
            return
            
        # Initialize request tracking if not exists
        if product_id not in self.active_requests:
            self.active_requests[product_id] = {
                'product_id': product_id,
                'product_name': offer_data.get('product_name'),
                'offers': [],
                'start_time': datetime.utcnow(),
                'status': 'collecting_offers'
            }
            
        # Validate offer using LLM (optional enhancement)
        validated_offer = await self._validate_offer(offer_data)
        
        # Add offer to collection
        self.active_requests[product_id]['offers'].append(validated_offer)
        
        self.logger.info(f"Received offer from {offer_data.get('supplier_name')} for {offer_data.get('product_name')}")
        
        # Check if we have enough offers or should evaluate now
        offers_count = len(self.active_requests[product_id]['offers'])
        if offers_count >= 3 or self._should_evaluate_early(product_id):
            await self.evaluate_offers(product_id)
            
    async def _validate_offer(self, offer_data: Dict) -> Dict:
        """Validate offer data and add LLM insights"""
        # Basic validation
        required_fields = ['supplier_name', 'quantity', 'unit_price', 'total_price', 'delivery_days']
        for field in required_fields:
            if field not in offer_data:
                self.logger.warning(f"Offer missing required field: {field}")
                
        # Add validation timestamp and score
        offer_data['validated_at'] = datetime.utcnow().isoformat()
        offer_data['validation_score'] = self._calculate_validation_score(offer_data)
        
        return offer_data
    
    def _calculate_validation_score(self, offer_data: Dict) -> float:
        """Calculate validation score for offer"""
        score = 1.0
        
        # Check for reasonable pricing
        unit_price = offer_data.get('unit_price', 0)
        if unit_price <= 0:
            score -= 0.3
        elif unit_price > 1000:  # Suspiciously high
            score -= 0.2
            
        # Check delivery time
        delivery_days = offer_data.get('delivery_days', 0)
        if delivery_days <= 0 or delivery_days > 30:
            score -= 0.2
            
        # Check LLM confidence if available
        llm_confidence = offer_data.get('llm_confidence', 1.0)
        score *= llm_confidence
        
        return max(0.0, score)
    
    def _should_evaluate_early(self, product_id: str) -> bool:
        """Determine if we should evaluate offers early"""
        request = self.active_requests.get(product_id, {})
        alert_data = request.get('alert_data', {})
        
        # Evaluate early for critical urgency
        if alert_data.get('urgency') == 'critical':
            return len(request.get('offers', [])) >= 2
            
        return False
        
    async def set_offer_timeout(self, product_id: str, timeout_seconds: int):
        """Set timeout for offer collection"""
        await asyncio.sleep(timeout_seconds)
        
        if (product_id in self.active_requests and 
            self.active_requests[product_id]['status'] == 'collecting_offers'):
            await self.evaluate_offers(product_id)
            
    async def evaluate_offers(self, product_id: str):
        """Evaluate collected offers using LLM intelligence"""
        if product_id not in self.active_requests:
            return
            
        request = self.active_requests[product_id]
        offers = request['offers']
        
        if not offers:
            self.logger.warning(f"No offers received for {product_id}")
            return
            
        self.logger.info(f"Evaluating {len(offers)} offers for {request['product_name']}")
        
        # Use LLM to evaluate offers
        evaluation = await self.llm_service.evaluate_offers(offers, self.selection_criteria)
        
        if evaluation and 'recommendation' in evaluation:
            # Find the recommended offer
            recommended_supplier = evaluation['recommendation']['selected_supplier']
            best_offer = None
            
            for offer in offers:
                if offer['supplier_name'] == recommended_supplier:
                    best_offer = offer
                    break
                    
            if best_offer:
                request['selected_offer'] = best_offer
                request['evaluation'] = evaluation
                request['status'] = 'awaiting_approval'
                
                # Generate comprehensive manager report
                alert_data = request.get('alert_data', {})
                urgency_level = alert_data.get('urgency', 'medium')
                
                manager_report = await self.llm_service.generate_manager_report(
                    evaluation, alert_data, urgency_level
                )
                
                request['manager_report'] = manager_report
                
                # Send for manager approval
                await self.request_manager_approval(product_id, best_offer, evaluation, manager_report)
            else:
                self.logger.error(f"Could not find recommended offer from {recommended_supplier}")
        else:
            self.logger.error(f"Failed to evaluate offers for {product_id}")
            
    async def request_manager_approval(self, product_id: str, offer: Dict, 
                                     evaluation: Dict, report: Dict):
        """Send approval request to manager with LLM-generated report"""
        request = self.active_requests[product_id]
        
        # Prepare comprehensive approval data
        approval_data = {
            'type': 'approval_request',
            'request_id': f"REQ_{product_id}_{int(datetime.utcnow().timestamp())}",
            'product_id': product_id,
            'product_name': offer['product_name'],
            'selected_offer': offer,
            'evaluation': evaluation,
            'manager_report': report,
            'alternatives': len(request['offers']) - 1,
            'urgency': offer.get('urgency', 'medium'),
            'total_cost': offer['total_price'],
            'delivery_date': offer['delivery_date'],
            'llm_recommendation': evaluation.get('recommendation', {}),
            'risk_assessment': evaluation.get('ranking', [{}])[0].get('risks', []),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to manager agent
        manager_address = AgentAddress("manager_agent")
        await self.send_message(manager_address, approval_data, MessageType.REQUEST)
        
        self.logger.info(f"Sent LLM-enhanced approval request for {offer['product_name']}")
        
    async def handle_manager_approval(self, message):
        """Handle manager approval/rejection"""
        approval_data = message.content
        request_id = approval_data.get('request_id')
        decision = approval_data.get('decision')  # 'approved' or 'rejected'
        
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
        """Process approved order with LLM-generated communications"""
        # Generate order confirmation message
        order_context = {
            'product_name': offer['product_name'],
            'supplier_name': offer['supplier_name'],
            'quantity': offer['quantity'],
            'total_price': offer['total_price'],
            'delivery_date': offer['delivery_date']
        }
        
        order_message = await self.llm_service.generate_communication_message(
            'order_confirmation', order_context
        )
        
        # Send order confirmation to supplier
        supplier_address = AgentAddress(f"supplier_agent_{offer['supplier_id']}")
        order_data = {
            'type': 'order_confirmation',
            'order': offer,
            'confirmation_message': order_message
        }
        
        await self.send_message(supplier_address, order_data, MessageType.REQUEST)
        
        # Notify inventory agent of incoming stock
        inventory_address = AgentAddress("inventory_agent")
        inventory_update = {
            'type': 'incoming_stock',
            'product_id': product_id,
            'quantity': offer['quantity'],
            'expected_date': offer['delivery_date'],
            'supplier': offer['supplier_name'],
            'order_id': offer.get('offer_id')
        }
        
        await self.send_message(inventory_address, inventory_update, MessageType.NOTIFICATION)
        
        self.logger.info(f"Order processed for {offer['product_name']} - LLM enhanced workflow")
        
    async def handle_rejected_order(self, product_id: str, reason: str):
        """Handle rejected order with LLM analysis"""
        self.logger.info(f"Order rejected for {product_id}: {reason}")
        
        # Could use LLM to analyze rejection reasons and suggest alternatives
        # For now, just log the rejection
        
    async def get_manager_status(self) -> Dict:
        """Get current stock manager status with LLM insights"""
        active_evaluations = 0
        pending_approvals = 0
        
        for request in self.active_requests.values():
            if request['status'] == 'collecting_offers':
                active_evaluations += 1
            elif request['status'] == 'awaiting_approval':
                pending_approvals += 1
                
        return {
            'agent_id': self.address.agent_id,
            'status': self.state,
            'active_requests': len(self.active_requests),
            'active_evaluations': active_evaluations,
            'pending_approvals': pending_approvals,
            'llm_enabled': True,
            'selection_criteria': self.selection_criteria,
            'last_activity': datetime.utcnow().isoformat()
        }