"""
Google Gemini LLM Integration for A2A Agents
"""

import google.generativeai as genai
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LLMResponse:
    content: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any]

class GeminiLLMService:
    """Service for integrating Google Gemini LLM with A2A agents"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-pro"):
        self.api_key = api_key
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Initialize conversation history for context
        self.conversation_history = {}
    
    async def generate_supplier_offer(self, product_info: Dict, supplier_profile: Dict, 
                                    market_conditions: Dict) -> Dict[str, Any]:
        """Generate intelligent supplier offer using Gemini"""
        
        prompt = f"""
        You are an AI agent representing {supplier_profile['name']}, a supplier with the following profile:
        - Location: {supplier_profile['location']}
        - Pricing Strategy: {supplier_profile['pricing_strategy']}
        - Reliability Score: {supplier_profile.get('reliability', 0.8)}
        - Specialties: {supplier_profile.get('specialties', [])}
        
        A company needs to restock the following product:
        - Product: {product_info['name']}
        - Current Stock: {product_info['current_stock']}
        - Threshold: {product_info['threshold']}
        - Category: {product_info['category']}
        - Urgency: {product_info.get('urgency', 'medium')}
        
        Market Conditions:
        - Base Price: ${product_info.get('base_price', 100)}
        - Market Demand: {market_conditions.get('demand', 'normal')}
        - Supply Chain Status: {market_conditions.get('supply_chain', 'normal')}
        - Seasonal Factor: {market_conditions.get('seasonal_factor', 1.0)}
        
        Generate a competitive offer including:
        1. Quantity to offer (minimum {product_info.get('min_quantity', 50)} units)
        2. Unit price (consider your pricing strategy and market conditions)
        3. Total price
        4. Delivery time in days
        5. Special terms or conditions
        6. Confidence level (0-1) in your ability to fulfill
        7. Brief reasoning for your pricing
        
        Respond in JSON format:
        {{
            "quantity": <number>,
            "unit_price": <number>,
            "total_price": <number>,
            "delivery_days": <number>,
            "special_terms": "<string>",
            "confidence": <number>,
            "reasoning": "<string>",
            "competitive_advantages": ["<advantage1>", "<advantage2>"]
        }}
        """
        
        try:
            response = await self._generate_response(prompt)
            offer_data = json.loads(response.content)
            
            # Add supplier metadata
            offer_data.update({
                'supplier_id': supplier_profile['id'],
                'supplier_name': supplier_profile['name'],
                'location': supplier_profile['location'],
                'generated_at': datetime.utcnow().isoformat(),
                'llm_confidence': response.confidence
            })
            
            self.logger.info(f"Generated offer for {supplier_profile['name']}: ${offer_data['total_price']}")
            return offer_data
            
        except Exception as e:
            self.logger.error(f"Error generating supplier offer: {e}")
            return self._fallback_offer(product_info, supplier_profile)
    
    async def evaluate_offers(self, offers: List[Dict], evaluation_criteria: Dict) -> Dict[str, Any]:
        """Use Gemini to evaluate and rank supplier offers"""
        
        offers_summary = []
        for offer in offers:
            offers_summary.append({
                'supplier': offer['supplier_name'],
                'price': offer['total_price'],
                'delivery': offer['delivery_days'],
                'quantity': offer['quantity'],
                'confidence': offer.get('confidence', 0.8),
                'advantages': offer.get('competitive_advantages', [])
            })
        
        prompt = f"""
        You are an AI procurement specialist evaluating supplier offers. 
        
        Evaluation Criteria (weights):
        - Price Weight: {evaluation_criteria.get('price_weight', 0.4)}
        - Speed Weight: {evaluation_criteria.get('speed_weight', 0.3)}
        - Reliability Weight: {evaluation_criteria.get('reliability_weight', 0.3)}
        - Quality Weight: {evaluation_criteria.get('quality_weight', 0.0)}
        
        Supplier Offers:
        {json.dumps(offers_summary, indent=2)}
        
        Analyze each offer and provide:
        1. Ranking of offers (1st, 2nd, 3rd choice)
        2. Score for each offer (0-100)
        3. Detailed reasoning for the ranking
        4. Risk assessment for each supplier
        5. Recommendation with justification
        6. Alternative scenarios (if budget constraints, if urgent delivery needed)
        
        Respond in JSON format:
        {{
            "ranking": [
                {{
                    "rank": 1,
                    "supplier": "<name>",
                    "score": <number>,
                    "reasoning": "<detailed reasoning>",
                    "risks": ["<risk1>", "<risk2>"],
                    "advantages": ["<advantage1>", "<advantage2>"]
                }}
            ],
            "recommendation": {{
                "selected_supplier": "<name>",
                "justification": "<detailed justification>",
                "total_value": <number>,
                "confidence": <number>
            }},
            "alternatives": {{
                "budget_constrained": "<supplier_name>",
                "urgent_delivery": "<supplier_name>",
                "quality_focused": "<supplier_name>"
            }},
            "market_insights": "<insights about current market conditions>"
        }}
        """
        
        try:
            response = await self._generate_response(prompt)
            evaluation = json.loads(response.content)
            
            evaluation['evaluated_at'] = datetime.utcnow().isoformat()
            evaluation['llm_confidence'] = response.confidence
            
            self.logger.info(f"Evaluated {len(offers)} offers, recommended: {evaluation['recommendation']['selected_supplier']}")
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Error evaluating offers: {e}")
            return self._fallback_evaluation(offers)
    
    async def generate_manager_report(self, evaluation: Dict, product_info: Dict, 
                                    urgency_level: str) -> Dict[str, Any]:
        """Generate comprehensive manager report using Gemini"""
        
        prompt = f"""
        You are an AI assistant preparing a procurement report for a manager.
        
        Product Information:
        - Product: {product_info['name']}
        - Current Stock: {product_info['current_stock']} units
        - Threshold: {product_info['threshold']} units
        - Urgency: {urgency_level}
        
        Supplier Evaluation Results:
        {json.dumps(evaluation, indent=2)}
        
        Generate a comprehensive manager report including:
        1. Executive Summary (2-3 sentences)
        2. Situation Analysis (current stock status, urgency assessment)
        3. Supplier Comparison (key differences between top 3 offers)
        4. Recommendation with clear justification
        5. Financial Impact (cost analysis, budget implications)
        6. Risk Assessment (delivery risks, supplier reliability)
        7. Timeline (expected delivery, impact on operations)
        8. Action Required (what the manager needs to approve/decide)
        9. Alternative Options (if primary recommendation is rejected)
        
        Use professional business language, be concise but comprehensive.
        Include specific numbers and data points.
        
        Respond in JSON format:
        {{
            "executive_summary": "<summary>",
            "situation_analysis": "<analysis>",
            "supplier_comparison": "<comparison>",
            "recommendation": {{
                "supplier": "<name>",
                "justification": "<justification>",
                "total_cost": <number>,
                "delivery_timeline": "<timeline>"
            }},
            "financial_impact": "<impact analysis>",
            "risk_assessment": "<risk analysis>",
            "timeline": "<detailed timeline>",
            "action_required": "<specific actions>",
            "alternatives": "<alternative options>",
            "urgency_indicator": "<high/medium/low>",
            "approval_recommendation": "<approve/review/reject>"
        }}
        """
        
        try:
            response = await self._generate_response(prompt)
            report = json.loads(response.content)
            
            report.update({
                'generated_at': datetime.utcnow().isoformat(),
                'report_id': f"RPT_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'llm_confidence': response.confidence
            })
            
            self.logger.info(f"Generated manager report for {product_info['name']}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating manager report: {e}")
            return self._fallback_report(evaluation, product_info)
    
    async def generate_communication_message(self, message_type: str, context: Dict) -> str:
        """Generate contextual communication messages"""
        
        prompts = {
            'stock_alert': f"""
            Generate a professional stock alert message for:
            Product: {context['product_name']}
            Current Stock: {context['current_stock']}
            Threshold: {context['threshold']}
            Urgency: {context['urgency']}
            
            Make it clear, actionable, and professional.
            """,
            
            'offer_request': f"""
            Generate a supplier offer request message for:
            Product: {context['product_name']}
            Quantity Needed: {context['quantity']}
            Urgency: {context['urgency']}
            Delivery Requirements: {context.get('delivery_requirements', 'Standard')}
            
            Be professional and include all necessary details.
            """,
            
            'approval_email': f"""
            Generate a manager approval email for:
            Product: {context['product_name']}
            Recommended Supplier: {context['supplier_name']}
            Total Cost: ${context['total_cost']}
            Delivery Time: {context['delivery_days']} days
            Urgency: {context['urgency']}
            
            Include clear action items and decision points.
            """
        }
        
        prompt = prompts.get(message_type, f"Generate a {message_type} message with context: {context}")
        
        try:
            response = await self._generate_response(prompt)
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error generating {message_type} message: {e}")
            return f"System message: {message_type} for {context.get('product_name', 'product')}"
    
    async def _generate_response(self, prompt: str) -> LLMResponse:
        """Generate response using Gemini with error handling"""
        try:
            response = self.model.generate_content(prompt)
            
            # Extract confidence and reasoning (simplified)
            confidence = 0.8  # Default confidence
            reasoning = "Generated using Gemini LLM"
            
            return LLMResponse(
                content=response.text,
                confidence=confidence,
                reasoning=reasoning,
                metadata={'model': self.model_name, 'timestamp': datetime.utcnow().isoformat()}
            )
            
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            raise
    
    def _fallback_offer(self, product_info: Dict, supplier_profile: Dict) -> Dict[str, Any]:
        """Fallback offer generation if LLM fails"""
        base_price = product_info.get('base_price', 100)
        quantity = max(product_info.get('min_quantity', 50), product_info['threshold'] - product_info['current_stock'])
        
        # Simple pricing based on strategy
        if supplier_profile['pricing_strategy'] == 'competitive':
            unit_price = base_price * 0.9
            delivery_days = 5
        elif supplier_profile['pricing_strategy'] == 'premium':
            unit_price = base_price * 1.2
            delivery_days = 2
        else:
            unit_price = base_price
            delivery_days = 3
        
        return {
            'quantity': quantity,
            'unit_price': unit_price,
            'total_price': unit_price * quantity,
            'delivery_days': delivery_days,
            'special_terms': 'Standard terms',
            'confidence': 0.6,
            'reasoning': 'Fallback pricing algorithm',
            'competitive_advantages': ['Reliable delivery'],
            'supplier_id': supplier_profile['id'],
            'supplier_name': supplier_profile['name'],
            'location': supplier_profile['location'],
            'generated_at': datetime.utcnow().isoformat(),
            'llm_confidence': 0.0
        }
    
    def _fallback_evaluation(self, offers: List[Dict]) -> Dict[str, Any]:
        """Fallback evaluation if LLM fails"""
        if not offers:
            return {'error': 'No offers to evaluate'}
        
        # Simple scoring based on price
        ranked_offers = sorted(offers, key=lambda x: x['total_price'])
        
        return {
            'ranking': [
                {
                    'rank': i + 1,
                    'supplier': offer['supplier_name'],
                    'score': 100 - (i * 10),
                    'reasoning': f'Ranked by price: ${offer["total_price"]}',
                    'risks': ['Standard delivery risk'],
                    'advantages': ['Competitive pricing']
                }
                for i, offer in enumerate(ranked_offers[:3])
            ],
            'recommendation': {
                'selected_supplier': ranked_offers[0]['supplier_name'],
                'justification': 'Lowest price option',
                'total_value': ranked_offers[0]['total_price'],
                'confidence': 0.6
            },
            'evaluated_at': datetime.utcnow().isoformat(),
            'llm_confidence': 0.0
        }
    
    def _fallback_report(self, evaluation: Dict, product_info: Dict) -> Dict[str, Any]:
        """Fallback report generation if LLM fails"""
        return {
            'executive_summary': f"Procurement request for {product_info['name']} requires manager approval.",
            'situation_analysis': f"Current stock ({product_info['current_stock']}) below threshold ({product_info['threshold']}).",
            'recommendation': evaluation.get('recommendation', {}),
            'action_required': 'Manager approval needed for purchase order',
            'generated_at': datetime.utcnow().isoformat(),
            'report_id': f"RPT_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'llm_confidence': 0.0
        }