"""
Email Service for sending notifications to managers
Handles approval requests and system alerts
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from datetime import datetime

class EmailService:
    def __init__(self, config: Dict):
        self.config = config
        self.smtp_server = config['smtp_server']
        self.smtp_port = config['smtp_port']
        self.username = config['username']
        self.password = config['password']
        self.from_email = config['from_email']
        self.manager_emails = config['manager_emails']
        self.logger = logging.getLogger(__name__)
        
    async def send_approval_request(self, approval_data: Dict):
        """Send approval request email to manager"""
        subject = f"Stock Purchase Approval Required - {approval_data['product_name']}"
        
        html_body = self._create_approval_email_html(approval_data)
        text_body = self._create_approval_email_text(approval_data)
        
        await self._send_email(
            to_emails=self.manager_emails,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        
        self.logger.info(f"Approval request email sent for {approval_data['product_name']}")
        
    def _create_approval_email_html(self, data: Dict) -> str:
        """Create HTML email for approval request"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .offer-details {{ background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #007bff; }}
                .urgency-high {{ border-left-color: #dc3545 !important; }}
                .urgency-medium {{ border-left-color: #ffc107 !important; }}
                .buttons {{ text-align: center; margin: 20px 0; }}
                .btn {{ display: inline-block; padding: 10px 20px; margin: 0 10px; text-decoration: none; border-radius: 5px; }}
                .btn-approve {{ background: #28a745; color: white; }}
                .btn-reject {{ background: #dc3545; color: white; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Stock Purchase Approval Required</h1>
                </div>
                
                <div class="content">
                    <h2>Request Details</h2>
                    <div class="offer-details urgency-{data.get('urgency', 'medium')}">
                        <h3>{data['product_name']}</h3>
                        <p><strong>Request ID:</strong> {data['request_id']}</p>
                        <p><strong>Urgency:</strong> {data.get('urgency', 'medium').upper()}</p>
                        
                        <table>
                            <tr><th>Supplier</th><td>{data['selected_offer']['supplier_name']}</td></tr>
                            <tr><th>Quantity</th><td>{data['selected_offer']['quantity']} units</td></tr>
                            <tr><th>Unit Price</th><td>${data['selected_offer']['unit_price']:.2f}</td></tr>
                            <tr><th>Total Cost</th><td>${data['selected_offer']['total_price']:.2f}</td></tr>
                            <tr><th>Delivery Time</th><td>{data['selected_offer']['delivery_days']} days</td></tr>
                            <tr><th>Expected Delivery</th><td>{data['selected_offer']['delivery_date'][:10]}</td></tr>
                        </table>
                        
                        <p><strong>Alternative Offers Considered:</strong> {data['alternatives']}</p>
                    </div>
                    
                    <div class="buttons">
                        <a href="mailto:{self.from_email}?subject=APPROVE {data['request_id']}&body=I approve this purchase request." class="btn btn-approve">
                            APPROVE
                        </a>
                        <a href="mailto:{self.from_email}?subject=REJECT {data['request_id']}&body=I reject this purchase request. Reason:" class="btn btn-reject">
                            REJECT
                        </a>
                    </div>
                    
                    <p><em>Please reply to this email with your decision or use the buttons above.</em></p>
                    <p><em>Request generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        
    def _create_approval_email_text(self, data: Dict) -> str:
        """Create plain text email for approval request"""
        return f"""
STOCK PURCHASE APPROVAL REQUIRED

Request Details:
- Product: {data['product_name']}
- Request ID: {data['request_id']}
- Urgency: {data.get('urgency', 'medium').upper()}

Selected Offer:
- Supplier: {data['selected_offer']['supplier_name']}
- Quantity: {data['selected_offer']['quantity']} units
- Unit Price: ${data['selected_offer']['unit_price']:.2f}
- Total Cost: ${data['selected_offer']['total_price']:.2f}
- Delivery Time: {data['selected_offer']['delivery_days']} days
- Expected Delivery: {data['selected_offer']['delivery_date'][:10]}

Alternative offers considered: {data['alternatives']}

To approve this request, reply to this email with "APPROVE {data['request_id']}"
To reject this request, reply to this email with "REJECT {data['request_id']} [reason]"

Request generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
        """
        
    async def send_approval_notification(self, approval_data: Dict):
        """Send approval notification (same as approval request for now)"""
        await self.send_approval_request(approval_data)
        
    async def send_order_confirmation(self, order_data: Dict):
        """Send order confirmation email"""
        subject = f"Order Confirmed - {order_data['product_name']}"
        
        html_body = f"""
        <h2>Order Confirmation</h2>
        <p>Your order has been confirmed and sent to the supplier.</p>
        
        <h3>Order Details:</h3>
        <ul>
            <li><strong>Product:</strong> {order_data['product_name']}</li>
            <li><strong>Supplier:</strong> {order_data['supplier_name']}</li>
            <li><strong>Quantity:</strong> {order_data['quantity']} units</li>
            <li><strong>Total Cost:</strong> ${order_data['total_price']:.2f}</li>
            <li><strong>Expected Delivery:</strong> {order_data['delivery_date'][:10]}</li>
        </ul>
        
        <p>Tracking information will be provided when available.</p>
        """
        
        await self._send_email(
            to_emails=self.manager_emails,
            subject=subject,
            html_body=html_body
        )
        
    async def send_system_alert(self, alert_data: Dict):
        """Send system alert email"""
        subject = f"System Alert - {alert_data.get('level', 'INFO').upper()}"
        
        html_body = f"""
        <h2>System Alert</h2>
        <p><strong>Level:</strong> {alert_data.get('level', 'INFO').upper()}</p>
        <p><strong>Message:</strong> {alert_data['message']}</p>
        <p><strong>Time:</strong> {alert_data.get('timestamp', datetime.utcnow().isoformat())}</p>
        
        {f"<p><strong>Agent:</strong> {alert_data['agent_id']}</p>" if alert_data.get('agent_id') else ""}
        """
        
        await self._send_email(
            to_emails=self.manager_emails,
            subject=subject,
            html_body=html_body
        )
        
    async def _send_email(self, to_emails: List[str], subject: str, 
                         html_body: str, text_body: str = None):
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # Add text part
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
                
            # Add HTML part
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.config.get('use_tls', True):
                    server.starttls()
                    
                if self.username and self.password:
                    server.login(self.username, self.password)
                    
                server.send_message(msg)
                
            self.logger.info(f"Email sent successfully: {subject}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            raise
            
    async def check_approval_responses(self) -> List[Dict]:
        """Check for email responses with approval decisions"""
        # This would integrate with IMAP to check for replies
        # Mock implementation for now
        return []