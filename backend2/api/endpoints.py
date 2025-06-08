"""
FastAPI endpoints for the A2A Stock Management System
Provides REST API for frontend integration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import asyncio
import logging
from datetime import datetime

from core.a2a_framework import A2ARegistry, RedisTransport
from core.gemini_integration import GeminiLLMService
from agents.inventory_agent import InventoryAgent
from agents.supplier_agent import SupplierAgent
from agents.stock_manager_agent import StockManagerAgent
from agents.manager_agent import ManagerAgent
from config.config import Config

app = FastAPI(title="A2A Stock Management System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for agents and services
config = None
transport = None
registry = None
llm_service = None
agents = {}
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize the A2A system on startup"""
    global config, transport, registry, llm_service, agents
    
    try:
        # Load configuration
        config = Config()
        
        # Initialize transport
        transport = RedisTransport()
        
        # Initialize registry
        import redis
        redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
        registry = A2ARegistry(redis_client)
        
        # Initialize LLM service
        llm_service = GeminiLLMService(
            api_key=config.gemini.api_key,
            model_name=config.gemini.model_name
        )
        
        # Initialize agents
        agents['inventory'] = InventoryAgent(config, transport, llm_service)
        agents['stock_manager'] = StockManagerAgent(config, transport, llm_service)
        agents['manager'] = ManagerAgent(config, transport, llm_service)
        
        # Initialize supplier agents
        for supplier_id, supplier_config in config.suppliers.items():
            agent_key = f'supplier_{supplier_id}'
            agents[agent_key] = SupplierAgent(
                supplier_id, supplier_config.name, config, transport, llm_service
            )
        
        # Start all agents
        for agent in agents.values():
            await agent.start()
            await registry.register_agent(agent)
            
        logger.info("A2A Stock Management System started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start system: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global agents
    
    try:
        for agent in agents.values():
            await agent.stop()
        logger.info("A2A Stock Management System stopped")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/api/status")
async def get_system_status():
    """Get overall system status"""
    try:
        agent_statuses = []
        for agent_key, agent in agents.items():
            status = agent.get_status()
            agent_statuses.append({
                'id': agent_key,
                'name': agent.address.agent_id,
                'type': agent_key.split('_')[0],
                'status': status['state'],
                'lastActivity': status['timestamp'],
                'capabilities': status.get('capabilities', {}),
                'location': getattr(agent, 'location', None)
            })
        
        return {
            'systemStatus': 'running',
            'totalAgents': len(agents),
            'agents': agent_statuses,
            'lastUpdate': datetime.utcnow().isoformat(),
            'llmEnabled': True
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/inventory")
async def get_inventory_status():
    """Get current inventory status"""
    try:
        if 'inventory' not in agents:
            raise HTTPException(status_code=503, detail="Inventory agent not available")
            
        inventory_agent = agents['inventory']
        status = await inventory_agent.get_inventory_status()
        
        # Transform for frontend
        inventory_items = []
        for item in status.get('items', []):
            inventory_items.append({
                'id': item['product_id'],
                'name': item['product_name'],
                'currentStock': item['current_stock'],
                'threshold': item['threshold'],
                'unit': item.get('unit', 'units'),
                'category': item.get('category', 'General'),
                'urgency': item.get('urgency', 'normal')
            })
        
        return {
            'inventory': inventory_items,
            'totalProducts': status.get('total_products', 0),
            'lowStockItems': status.get('low_stock_items', 0),
            'criticalItems': status.get('critical_items', 0),
            'lastCheck': status.get('last_check')
        }
    except Exception as e:
        logger.error(f"Error getting inventory status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/offers")
async def get_active_offers():
    """Get active supplier offers"""
    try:
        if 'stock_manager' not in agents:
            raise HTTPException(status_code=503, detail="Stock manager agent not available")
            
        stock_manager = agents['stock_manager']
        status = await stock_manager.get_manager_status()
        
        # Get offers from active requests
        offers = []
        for request in stock_manager.active_requests.values():
            for offer in request.get('offers', []):
                offers.append({
                    'id': offer.get('offer_id'),
                    'supplierId': offer.get('supplier_id'),
                    'supplierName': offer.get('supplier_name'),
                    'productId': offer.get('product_id'),
                    'quantity': offer.get('quantity'),
                    'price': offer.get('total_price'),
                    'deliveryTime': offer.get('delivery_days'),
                    'timestamp': offer.get('timestamp'),
                    'status': 'pending',  # Default status
                    'llmConfidence': offer.get('llm_confidence', 0.8)
                })
        
        return {
            'offers': offers,
            'activeRequests': status.get('active_requests', 0),
            'llmEnabled': True
        }
    except Exception as e:
        logger.error(f"Error getting offers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/approvals")
async def get_pending_approvals():
    """Get pending manager approvals"""
    try:
        if 'manager' not in agents:
            raise HTTPException(status_code=503, detail="Manager agent not available")
            
        manager_agent = agents['manager']
        approvals_data = await manager_agent.get_pending_approvals()
        
        return {
            'pendingApprovals': approvals_data.get('requests', []),
            'count': approvals_data.get('count', 0),
            'autoApproveThreshold': approvals_data.get('auto_approve_threshold'),
            'llmEnabled': approvals_data.get('llm_enabled', True)
        }
    except Exception as e:
        logger.error(f"Error getting pending approvals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/approvals/{request_id}/approve")
async def approve_request(request_id: str, reason: str = ""):
    """Approve a pending request"""
    try:
        if 'manager' not in agents:
            raise HTTPException(status_code=503, detail="Manager agent not available")
            
        manager_agent = agents['manager']
        success = await manager_agent.approve_request(request_id, reason)
        
        if success:
            return {"status": "approved", "requestId": request_id}
        else:
            raise HTTPException(status_code=404, detail="Request not found")
            
    except Exception as e:
        logger.error(f"Error approving request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/approvals/{request_id}/reject")
async def reject_request(request_id: str, reason: str = ""):
    """Reject a pending request"""
    try:
        if 'manager' not in agents:
            raise HTTPException(status_code=503, detail="Manager agent not available")
            
        manager_agent = agents['manager']
        success = await manager_agent.reject_request(request_id, reason)
        
        if success:
            return {"status": "rejected", "requestId": request_id}
        else:
            raise HTTPException(status_code=404, detail="Request not found")
            
    except Exception as e:
        logger.error(f"Error rejecting request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_system_logs():
    """Get recent system logs"""
    try:
        # This would integrate with a proper logging system
        # For now, return mock logs
        logs = [
            {
                'id': 'log-001',
                'timestamp': datetime.utcnow().isoformat(),
                'level': 'info',
                'message': 'LLM-enhanced offer evaluation completed',
                'agentId': 'stock_manager_agent'
            },
            {
                'id': 'log-002',
                'timestamp': datetime.utcnow().isoformat(),
                'level': 'warning',
                'message': 'Stock level below threshold detected',
                'agentId': 'inventory_agent'
            }
        ]
        
        return {'logs': logs}
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulate/stock-depletion")
async def simulate_stock_depletion(product_id: str):
    """Simulate stock depletion for testing"""
    try:
        if 'inventory' not in agents:
            raise HTTPException(status_code=503, detail="Inventory agent not available")
            
        inventory_agent = agents['inventory']
        
        # Simulate stock update
        await inventory_agent.handle_stock_update(type('Message', (), {
            'content': {
                'type': 'stock_update',
                'updates': [{
                    'product_id': product_id,
                    'quantity': 40,  # Reduce stock significantly
                    'operation': 'subtract'
                }]
            },
            'sender': inventory_agent.address
        })())
        
        return {"status": "simulated", "productId": product_id}
        
    except Exception as e:
        logger.error(f"Error simulating stock depletion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get specific agent status"""
    try:
        if agent_id not in agents:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        agent = agents[agent_id]
        status = agent.get_status()
        
        # Add agent-specific information
        if hasattr(agent, 'get_inventory_status'):
            status['inventory_status'] = await agent.get_inventory_status()
        elif hasattr(agent, 'get_supplier_status'):
            status['supplier_status'] = await agent.get_supplier_status()
        elif hasattr(agent, 'get_manager_status'):
            status['manager_status'] = await agent.get_manager_status()
            
        return status
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)