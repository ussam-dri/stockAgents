"""
Manager Agent with Gemini LLM Integration
Handles approval decisions with LLM-generated reports and communications
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from core.a2a_framework import A2AAgent, AgentAddress, MessageType
from core.gemini_integration import GeminiLLMService
from config.config import Config
from notifications.email_service import EmailService

class ManagerAgent(A2AAgent):
    def __init__(self, config: Config, transport, llm_service: GeminiLLMService):
        super().__init__("manager_agent", transport)
        self.config = config
        self.llm_service = llm_service
        self.email_service = EmailService(config.email.__dict__)
        self.pending_approvals = {}  # Track pending approval requests
        self.auto_approve_threshold = config.manager.auto_approve_threshold
        
        self.capabilities = {
            'approval_processing': True,
            'llm_reports': True,
            'email_notifications': True,
            'risk_analysis': True
        }
        
        # Register message handlers
        self.register_handler('approval_request', self.handle_approval_request)
        self.register_handler('approval_decision', self.handle_approval_decision)
        
    async def start(self):
        """Start the manager agent"""
        await super().start()
        
        # Start approval interface monitoring
        asyncio.create_task(self.start_approval_interface())
        
        self.logger.info("Manager Agent started with LLM integration")
        
    async def handle_message(self, message):
        """Handle incoming messages"""
        content_type = message.content.get('type')
        
        if content_type == 'approval_request':
            await self.handle_approval_request(message)
        elif content_type == 'approval_decision':
            await self.handle_approval_decision(message)
        else:
            self.logger.warning(f"Unknown message type: {content_type}")
            
    async def handle_approval_request(self, message):
        """Handle approval request with LLM-enhanced processing"""
        approval_data = message.content
        request_id = approval_data.get('request_id')
        
        # Store pending approval with LLM insights
        self.pending_approvals[request_id] = {
            **approval_data,
            'received_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        
        # Check for auto-approval
        total_cost = approval_data.get('total_cost', 0)
        if (self.auto_approve_threshold and total_cost <= self.auto_approve_threshold):
            await self.auto_approve_request(request_id, approval_data)
        else:
            # Generate enhanced email notification using LLM
            await self.send_llm_enhanced_notification(approval_data)
            self.logger.info(f"Approval request {request_id} sent for manual review with LLM insights")
            
    async def auto_approve_request(self, request_id: str, approval_data: Dict):
        """Auto-approve request with LLM-generated justification"""
        if request_id not in self.pending_approvals:
            return
            
        # Generate auto-approval justification using LLM
        justification_context = {
            'product_name': approval_data.get('product_name'),
            'total_cost': approval_data.get('total_cost'),
            'threshold': self.auto_approve_threshold,
            'urgency': approval_data.get('urgency'),
            'supplier_name': approval_data.get('selected_offer', {}).get('supplier_name')
        }
        
        justification = await self.llm_service.generate_communication_message(
            'auto_approval_justification', justification_context
        )
        
        approval_record = self.pending_approvals[request_id]
        approval_record.update({
            'status': 'auto_approved',
            'approved_at': datetime.utcnow().isoformat(),
            'approved_by': 'system',
            'justification': justification
        })
        
        # Send approval back to stock manager
        response_data = {
            'type': 'manager_approval',
            'request_id': request_id,
            'decision': 'approved',
            'approved_by': 'system',
            'reason': justification,
            'auto_approved': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        stock_manager_address = AgentAddress("stock_manager_agent")
        await self.send_message(stock_manager_address, response_data, MessageType.RESPONSE)
        
        self.logger.info(f"Auto-approved request {request_id} with LLM justification")
        
    async def send_llm_enhanced_notification(self, approval_data: Dict):
        """Send LLM-enhanced email notification"""
        try:
            # Get the manager report from the approval data
            manager_report = approval_data.get('manager_report', {})
            
            # Generate additional email content using LLM
            email_context = {
                'product_name': approval_data.get('product_name'),
                'supplier_name': approval_data.get('selected_offer', {}).get('supplier_name'),
                'total_cost': approval_data.get('total_cost'),
                'delivery_days': approval_data.get('selected_offer', {}).get('delivery_days'),
                'urgency': approval_data.get('urgency'),
                'executive_summary': manager_report.get('executive_summary', ''),
                'recommendation': manager_report.get('recommendation', {}),
                'risk_assessment': manager_report.get('risk_assessment', '')
            }
            
            email_content = await self.llm_service.generate_communication_message(
                'approval_email', email_context
            )
            
            # Enhance the approval data with LLM-generated content
            enhanced_approval_data = {
                **approval_data,
                'llm_email_content': email_content,
                'manager_report': manager_report
            }
            
            # Send enhanced email notification
            await self.email_service.send_llm_enhanced_approval_request(enhanced_approval_data)
            
        except Exception as e:
            self.logger.error(f"Error sending LLM-enhanced notification: {e}")
            # Fallback to standard notification
            await self.email_service.send_approval_request(approval_data)
            
    async def handle_approval_decision(self, message):
        """Handle manual approval decision with LLM analysis"""
        decision_data = message.content
        request_id = decision_data.get('request_id')
        
        if request_id not in self.pending_approvals:
            self.logger.error(f"Unknown approval request: {request_id}")
            return
            
        approval_record = self.pending_approvals[request_id]
        approval_record.update({
            'status': decision_data.get('decision'),
            'approved_at': datetime.utcnow().isoformat(),
            'approved_by': decision_data.get('approved_by', 'manager'),
            'reason': decision_data.get('reason', '')
        })
        
        # Generate decision analysis using LLM
        decision_context = {
            'decision': decision_data.get('decision'),
            'product_name': approval_record.get('product_name'),
            'reason': decision_data.get('reason', ''),
            'total_cost': approval_record.get('total_cost'),
            'urgency': approval_record.get('urgency')
        }
        
        decision_analysis = await self.llm_service.generate_communication_message(
            'decision_analysis', decision_context
        )
        
        # Send decision back to stock manager
        response_data = {
            'type': 'manager_approval',
            'request_id': request_id,
            'decision': decision_data.get('decision'),
            'approved_by': decision_data.get('approved_by', 'manager'),
            'reason': decision_data.get('reason', ''),
            'llm_analysis': decision_analysis,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        stock_manager_address = AgentAddress("stock_manager_agent")
        await self.send_message(stock_manager_address, response_data, MessageType.RESPONSE)
        
        self.logger.info(f"Processed manual decision for {request_id}: {decision_data.get('decision')}")
        
    async def start_approval_interface(self):
        """Start web interface for approvals with LLM insights"""
        while self.running:
            try:
                # Check for email-based approvals
                await self.check_email_approvals()
                
                # Generate periodic status reports using LLM
                if len(self.pending_approvals) > 0:
                    await self.generate_status_report()
                    
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in approval interface: {e}")
                await asyncio.sleep(60)
                
    async def check_email_approvals(self):
        """Check for email-based approval responses"""
        # This would integrate with email service to check for replies
        # Implementation would parse email responses for approval/rejection
        pass
        
    async def generate_status_report(self):
        """Generate periodic status report using LLM"""
        if not self.pending_approvals:
            return
            
        # Prepare status data for LLM
        status_context = {
            'pending_count': len(self.pending_approvals),
            'requests': list(self.pending_approvals.values()),
            'auto_approve_threshold': self.auto_approve_threshold
        }
        
        try:
            status_report = await self.llm_service.generate_communication_message(
                'status_report', status_context
            )
            
            self.logger.info(f"Generated status report: {len(self.pending_approvals)} pending approvals")
            
        except Exception as e:
            self.logger.error(f"Error generating status report: {e}")
            
    async def approve_request(self, request_id: str, reason: str = "") -> bool:
        """Approve a pending request"""
        if request_id not in self.pending_approvals:
            return False
            
        decision_data = {
            'request_id': request_id,
            'decision': 'approved',
            'approved_by': 'manager',
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.handle_approval_decision(type('Message', (), {
            'content': decision_data,
            'sender': self.address
        })())
        
        return True
        
    async def reject_request(self, request_id: str, reason: str = "") -> bool:
        """Reject a pending request"""
        if request_id not in self.pending_approvals:
            return False
            
        decision_data = {
            'request_id': request_id,
            'decision': 'rejected',
            'approved_by': 'manager',
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.handle_approval_decision(type('Message', (), {
            'content': decision_data,
            'sender': self.address
        })())
        
        return True
        
    async def get_pending_approvals(self) -> Dict:
        """Get all pending approval requests with LLM insights"""
        enhanced_requests = []
        
        for request in self.pending_approvals.values():
            # Add LLM-generated summary for each request
            try:
                summary_context = {
                    'product_name': request.get('product_name'),
                    'total_cost': request.get('total_cost'),
                    'urgency': request.get('urgency'),
                    'supplier_name': request.get('selected_offer', {}).get('supplier_name')
                }
                
                summary = await self.llm_service.generate_communication_message(
                    'request_summary', summary_context
                )
                
                enhanced_request = {
                    **request,
                    'llm_summary': summary
                }
                enhanced_requests.append(enhanced_request)
                
            except Exception as e:
                self.logger.error(f"Error generating request summary: {e}")
                enhanced_requests.append(request)
                
        return {
            'count': len(self.pending_approvals),
            'requests': enhanced_requests,
            'auto_approve_threshold': self.auto_approve_threshold,
            'llm_enabled': True
        }
        
    async def get_manager_status(self) -> Dict:
        """Get current manager agent status with LLM insights"""
        return {
            'agent_id': self.address.agent_id,
            'status': self.state,
            'pending_approvals': len(self.pending_approvals),
            'auto_approve_threshold': self.auto_approve_threshold,
            'llm_enabled': True,
            'capabilities': self.capabilities,
            'last_activity': datetime.utcnow().isoformat()
        }