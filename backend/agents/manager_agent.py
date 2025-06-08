"""
Manager Agent - Handles approval decisions and email interactions
Provides interface for human manager to approve/reject orders
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from google_adk import Agent, Message, AgentAddress
from ..config.config import Config
from ..notifications.email_service import EmailService

class ManagerAgent(Agent):
    def __init__(self, config: Config):
        super().__init__(
            name="ManagerAgent",
            address=AgentAddress("manager", "localhost", 8006)
        )
        self.config = config
        self.email_service = EmailService(config.email)
        self.pending_approvals = {}  # Track pending approval requests
        self.auto_approve_threshold = config.manager.auto_approve_threshold
        self.logger = logging.getLogger(__name__)
        
    async def start(self):
        """Start the manager agent"""
        self.logger.info("Manager Agent starting...")
        await self.register()
        
        # Start web interface for approvals
        asyncio.create_task(self.start_approval_interface())
        
    async def handle_message(self, message: Message):
        """Handle incoming messages"""
        if message.message_type == "approval_request":
            await self.handle_approval_request(message)
        elif message.message_type == "approval_decision":
            await self.handle_approval_decision(message)
            
    async def handle_approval_request(self, message: Message):
        """Handle approval request from stock manager"""
        approval_data = message.content
        request_id = approval_data['request_id']
        
        # Store pending approval
        self.pending_approvals[request_id] = {
            **approval_data,
            'received_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        
        # Check for auto-approval
        if (self.auto_approve_threshold and 
            approval_data['total_cost'] <= self.auto_approve_threshold):
            await self.auto_approve_request(request_id)
        else:
            # Send email notification for manual approval
            await self.email_service.send_approval_notification(approval_data)
            self.logger.info(f"Approval request {request_id} sent for manual review")
            
    async def auto_approve_request(self, request_id: str):
        """Auto-approve request below threshold"""
        if request_id not in self.pending_approvals:
            return
            
        approval_data = self.pending_approvals[request_id]
        approval_data['status'] = 'auto_approved'
        approval_data['approved_at'] = datetime.utcnow().isoformat()
        approval_data['approved_by'] = 'system'
        
        # Send approval back to stock manager
        response = Message(
            sender=self.address,
            recipient=AgentAddress("stock_manager", "localhost", 8005),
            content={
                'request_id': request_id,
                'decision': 'approved',
                'approved_by': 'system',
                'reason': f'Auto-approved (amount ${approval_data["total_cost"]} below threshold)'
            },
            message_type="manager_approval"
        )
        
        await self.send_message(response)
        self.logger.info(f"Auto-approved request {request_id}")
        
    async def handle_approval_decision(self, message: Message):
        """Handle manual approval decision"""
        decision_data = message.content
        request_id = decision_data['request_id']
        
        if request_id not in self.pending_approvals:
            self.logger.error(f"Unknown approval request: {request_id}")
            return
            
        approval_data = self.pending_approvals[request_id]
        approval_data['status'] = decision_data['decision']
        approval_data['approved_at'] = datetime.utcnow().isoformat()
        approval_data['approved_by'] = decision_data.get('approved_by', 'manager')
        approval_data['reason'] = decision_data.get('reason', '')
        
        # Send decision back to stock manager
        response = Message(
            sender=self.address,
            recipient=AgentAddress("stock_manager", "localhost", 8005),
            content=decision_data,
            message_type="manager_approval"
        )
        
        await self.send_message(response)
        self.logger.info(f"Processed manual decision for {request_id}: {decision_data['decision']}")
        
    async def start_approval_interface(self):
        """Start web interface for approvals (simplified)"""
        # This would start a simple web server for manager approvals
        # For now, we'll simulate with periodic checks
        while True:
            await self.check_email_approvals()
            await asyncio.sleep(30)  # Check every 30 seconds
            
    async def check_email_approvals(self):
        """Check for email-based approval responses"""
        # This would integrate with email service to check for replies
        # Mock implementation for now
        pass
        
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
        
        await self.handle_approval_decision(Message(
            sender=self.address,
            recipient=self.address,
            content=decision_data,
            message_type="approval_decision"
        ))
        
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
        
        await self.handle_approval_decision(Message(
            sender=self.address,
            recipient=self.address,
            content=decision_data,
            message_type="approval_decision"
        ))
        
        return True
        
    async def get_pending_approvals(self) -> Dict:
        """Get all pending approval requests"""
        return {
            'count': len(self.pending_approvals),
            'requests': list(self.pending_approvals.values()),
            'auto_approve_threshold': self.auto_approve_threshold
        }
        
    async def get_manager_status(self) -> Dict:
        """Get current manager agent status"""
        return {
            'pending_approvals': len(self.pending_approvals),
            'auto_approve_threshold': self.auto_approve_threshold,
            'last_activity': datetime.utcnow().isoformat(),
            'status': 'active'
        }