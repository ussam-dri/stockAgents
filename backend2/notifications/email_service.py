"""
Enhanced Email Service with LLM-generated content
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
        
    async def send_llm_enhanced_approval_request(self, approval_data: Dict):
        """Send LLM-enhanced approval request email"""
        subject = f"🤖 AI-Enhanced Stock Purchase Approval - {approval_data['product_name']}"
        
        # Get LLM-generated content
        llm_content = approval_data.get('llm_email_content', '')
        manager_report = approval_data.get('manager_report', {})
        
        html_body = self._create_llm_enhanced_email_html(approval_data, llm_content, manager_report)
        text_body = self._create_llm_enhanced_email_text(approval_data, llm_content, manager_report)
        
        await self._send_email(
            to_emails=self.manager_emails,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        
        self.logger.info(f"LLM-enhanced approval email sent for {approval_data['product_name']}")
        
    def _create_llm_enhanced_email_html(self, data: Dict, llm_content: str, report: Dict) -> str:
        """Create LLM-enhanced HTML email"""
        selected_offer = data.get('selected_offer', {})
        evaluation = data.get('evaluation', {})
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; text-align: center; border-radius: 10px 10px 0 0; }}
                .ai-badge {{ background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px; display: inline-block; margin-top: 10px; }}
                .content {{ padding: 25px; background: #f8f9fa; }}
                .executive-summary {{ background: white; padding: 20px; margin: 20px 0; border-left: 5px solid #667eea; border-radius: 5px; }}
                .offer-details {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .urgency-critical {{ border-left-color: #dc3545 !important; }}
                .urgency-high {{ border-left-color: #fd7e14 !important; }}
                .urgency-medium {{ border-left-color: #ffc107 !important; }}
                .buttons {{ text-align: center; margin: 30px 0; }}
                .btn {{ display: inline-block; padding: 15px 30px; margin: 0 10px; text-decoration: none; border-radius: 8px; font-weight: bold; }}
                .btn-approve {{ background: #28a745; color: white; }}
                .btn-reject {{ background: #dc3545; color: white; }}
                .btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #f8f9fa; font-weight: 600; }}
                .llm-insight {{ background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .risk-assessment {{ background: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .recommendation {{ background: #d4edda; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 AI-Enhanced Procurement Decision</h1>
                    <div class="ai-badge">Powered by Gemini LLM</div>
                </div>
                
                <div class="content">
                    <div class="executive-summary">
                        <h2>📋 Executive Summary</h2>
                        <p>{report.get('executive_summary', 'AI analysis completed for procurement decision.')}</p>
                    </div>
                    
                    <div class="offer-details urgency-{data.get('urgency', 'medium')}">
                        <h3>🎯 Recommended Supplier: {selected_offer.get('supplier_name', 'N/A')}</h3>
                        <p><strong>Product:</strong> {data['product_name']}</p>
                        <p><strong>Request ID:</strong> {data['request_id']}</p>
                        <p><strong>Urgency Level:</strong> {data.get('urgency', 'medium').upper()}</p>
                        
                        <table>
                            <tr><th>Metric</th><th>Value</th><th>AI Assessment</th></tr>
                            <tr>
                                <td>Quantity</td>
                                <td>{selected_offer.get('quantity', 0)} units</td>
                                <td>✅ Optimal quantity</td>
                            </tr>
                            <tr>
                                <td>Unit Price</td>
                                <td>${selected_offer.get('unit_price', 0):.2f}</td>
                                <td>💰 Competitive pricing</td>
                            </tr>
                            <tr>
                                <td>Total Cost</td>
                                <td><strong>${selected_offer.get('total_price', 0):.2f}</strong></td>
                                <td>📊 Best value option</td>
                            </tr>
                            <tr>
                                <td>Delivery Time</td>
                                <td>{selected_offer.get('delivery_days', 0)} days</td>
                                <td>🚚 Meets requirements</td>
                            </tr>
                            <tr>
                                <td>Expected Delivery</td>
                                <td>{selected_offer.get('delivery_date', '')[:10]}</td>
                                <td>📅 On schedule</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="llm-insight">
                        <h3>🧠 AI Analysis</h3>
                        <p>{llm_content}</p>
                    </div>
                    
                    <div class="recommendation">
                        <h3>✅ AI Recommendation</h3>
                        <p><strong>Decision:</strong> {report.get('approval_recommendation', 'APPROVE').upper()}</p>
                        <p><strong>Confidence:</strong> {evaluation.get('recommendation', {}).get('confidence', 0.8) * 100:.0f}%</p>
                        <p><strong>Justification:</strong> {evaluation.get('recommendation', {}).get('justification', 'Best overall value proposition.')}</p>
                    </div>
                    
                    <div class="risk-assessment">
                        <h3>⚠️ Risk Assessment</h3>
                        <p>{report.get('risk_assessment', 'Standard procurement risks apply.')}</p>
                        <p><strong>Alternative Options:</strong> {data.get('alternatives', 0)} other suppliers evaluated</p>
                    </div>
                    
                    <div class="buttons">
                        <a href="mailto:{self.from_email}?subject=APPROVE {data['request_id']}&body=I approve this AI-recommended purchase request." class="btn btn-approve">
                            ✅ APPROVE RECOMMENDATION
                        </a>
                        <a href="mailto:{self.from_email}?subject=REJECT {data['request_id']}&body=I reject this purchase request. Reason:" class="btn btn-reject">
                            ❌ REJECT REQUEST
                        </a>
                    </div>
                    
                    <p style="text-align: center; color: #666; font-size: 14px; margin-top: 30px;">
                        <em>This analysis was generated by Gemini LLM and reviewed by the A2A system.<br>
                        Request generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</em>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
    def _create_llm_enhanced_email_text(self, data: Dict, llm_content: str, report: Dict) -> str:
        """Create LLM-enhanced plain text email"""
        selected_offer = data.get('selected_offer', {})
        evaluation = data.get('evaluation', {})
        
        return f"""
🤖 AI-ENHANCED STOCK PURCHASE APPROVAL REQUIRED

Executive Summary:
{report.get('executive_summary', 'AI analysis completed for procurement decision.')}

Product Details:
- Product: {data['product_name']}
- Request ID: {data['request_id']}
- Urgency Level: {data.get('urgency', 'medium').upper()}

AI-Recommended Supplier: {selected_offer.get('supplier_name', 'N/A')}
- Quantity: {selected_offer.get('quantity', 0)} units
- Unit Price: ${selected_offer.get('unit_price', 0):.2f}
- Total Cost: ${selected_offer.get('total_price', 0):.2f}
- Delivery Time: {selected_offer.get('delivery_days', 0)} days
- Expected Delivery: {selected_offer.get('delivery_date', '')[:10]}

AI Analysis:
{llm_content}

AI Recommendation: {report.get('approval_recommendation', 'APPROVE').upper()}
Confidence Level: {evaluation.get('recommendation', {}).get('confidence', 0.8) * 100:.0f}%
Justification: {evaluation.get('recommendation', {}).get('justification', 'Best overall value proposition.')}

Risk Assessment:
{report.get('risk_assessment', 'Standard procurement risks apply.')}

Alternative options evaluated: {data.get('alternatives', 0)} other suppliers

ACTIONS:
To approve: Reply with "APPROVE {data['request_id']}"
To reject: Reply with "REJECT {data['request_id']} [reason]"

This analysis was generated by Gemini LLM and reviewed by the A2A system.
Request generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
        """
        
    async def send_approval_request(self, approval_data: Dict):
        """Send standard approval request (fallback)"""
        subject = f"Stock Purchase Approval Required - {approval_data['product_name']}"
        
        html_body = self._create_approval_email_html(approval_data)
        text_body = self._create_approval_email_text(approval_data)
        
        await self._send_email(
            to_emails=self.manager_emails,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        
        self.logger.info(f"Standard approval request email sent for {approval_data['product_name']}")
        
    def _create_approval_email_html(self, data: Dict) -> str:
        """Create standard HTML email for approval request"""
        selected_offer = data.get('selected_offer', {})
        
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
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #f2f2f2; }}
                .buttons {{ text-align: center; margin: 20px 0; }}
                .btn {{ display: inline-block; padding: 10px 20px; margin: 0 10px; text-decoration: none; border-radius: 5px; }}
                .btn-approve {{ background: #28a745; color: white; }}
                .btn-reject {{ background: #dc3545; color: white; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Stock Purchase Approval Required</h1>
                </div>
                
                <div class="content">
                    <h2>Request Details</h2>
                    <div class="offer-details">
                        <h3>{data['product_name']}</h3>
                        <p><strong>Request ID:</strong> {data['request_id']}</p>
                        
                        <table>
                            <tr><th>Supplier</th><td>{selected_offer.get('supplier_name', 'N/A')}</td></tr>
                            <tr><th>Quantity</th><td>{selected_offer.get('quantity', 0)} units</td></tr>
                            <tr><th>Unit Price</th><td>${selected_offer.get('unit_price', 0):.2f}</td></tr>
                            <tr><th>Total Cost</th><td>${selected_offer.get('total_price', 0):.2f}</td></tr>
                            <tr><th>Delivery Time</th><td>{selected_offer.get('delivery_days', 0)} days</td></tr>
                        </table>
                    </div>
                    
                    <div class="buttons">
                        <a href="mailto:{self.from_email}?subject=APPROVE {data['request_id']}" class="btn btn-approve">
                            APPROVE
                        </a>
                        <a href="mailto:{self.from_email}?subject=REJECT {data['request_id']}" class="btn btn-reject">
                            REJECT
                        </a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
    def _create_approval_email_text(self, data: Dict) -> str:
        """Create standard plain text email for approval request"""
        selected_offer = data.get('selected_offer', {})
        
        return f"""
STOCK PURCHASE APPROVAL REQUIRED

Request Details:
- Product: {data['product_name']}
- Request ID: {data['request_id']}

Selected Offer:
- Supplier: {selected_offer.get('supplier_name', 'N/A')}
- Quantity: {selected_offer.get('quantity', 0)} units
- Unit Price: ${selected_offer.get('unit_price', 0):.2f}
- Total Cost: ${selected_offer.get('total_price', 0):.2f}
- Delivery Time: {selected_offer.get('delivery_days', 0)} days

To approve: Reply with "APPROVE {data['request_id']}"
To reject: Reply with "REJECT {data['request_id']} [reason]"

Request generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
        """
        
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