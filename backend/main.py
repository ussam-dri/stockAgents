"""
Main entry point for the A2A Stock Management System
Initializes and starts all agents
"""

import asyncio
import logging
import signal
import sys
from typing import List
from agents.inventory_agent import InventoryAgent
from agents.supplier_agent import SupplierAgent
from agents.stock_manager_agent import StockManagerAgent
from agents.manager_agent import ManagerAgent
from database.oracle_connection import OracleConnection
from config.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class A2AStockManagementSystem:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = Config(config_path)
        self.agents = []
        self.db = None
        self.logger = logging.getLogger(__name__)
        self.running = False
        
    async def initialize(self):
        """Initialize the system and all components"""
        self.logger.info("Initializing A2A Stock Management System...")
        
        # Initialize database
        self.db = OracleConnection(self.config.oracle.__dict__)
        await self.db.initialize()
        await self.db.create_tables()
        await self.db.seed_sample_data()
        
        # Create and initialize agents
        await self._create_agents()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("System initialization complete")
        
    async def _create_agents(self):
        """Create and initialize all agents"""
        # Create inventory agent
        inventory_agent = InventoryAgent(self.config)
        self.agents.append(inventory_agent)
        
        # Create supplier agents
        for supplier_id, supplier_config in self.config.suppliers.items():
            supplier_agent = SupplierAgent(
                supplier_id=supplier_id,
                supplier_name=supplier_config.name,
                config=self.config
            )
            self.agents.append(supplier_agent)
            
        # Create stock manager agent
        stock_manager_agent = StockManagerAgent(self.config)
        self.agents.append(stock_manager_agent)
        
        # Create manager agent
        manager_agent = ManagerAgent(self.config)
        self.agents.append(manager_agent)
        
        # Start all agents
        for agent in self.agents:
            await agent.start()
            
        self.logger.info(f"Started {len(self.agents)} agents")
        
    async def start(self):
        """Start the system"""
        self.running = True
        self.logger.info("A2A Stock Management System started")
        
        try:
            # Keep the system running
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        finally:
            await self.shutdown()
            
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False
        
    async def shutdown(self):
        """Gracefully shutdown the system"""
        self.logger.info("Shutting down A2A Stock Management System...")
        
        # Stop all agents
        for agent in self.agents:
            try:
                await agent.stop()
            except Exception as e:
                self.logger.error(f"Error stopping agent {agent.name}: {e}")
                
        # Close database connections
        if self.db:
            await self.db.close()
            
        self.logger.info("System shutdown complete")
        
    async def get_system_status(self) -> dict:
        """Get current system status"""
        try:
            agent_statuses = []
            for agent in self.agents:
                if hasattr(agent, 'get_agent_status'):
                    status = await agent.get_agent_status()
                    agent_statuses.append(status)
                    
            return {
                'system_running': self.running,
                'total_agents': len(self.agents),
                'agents': agent_statuses,
                'database_connected': self.db is not None,
                'timestamp': asyncio.get_event_loop().time()
            }
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}

async def main():
    """Main function"""
    system = A2AStockManagementSystem()
    
    try:
        await system.initialize()
        await system.start()
    except Exception as e:
        logging.error(f"System error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Create logs directory
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Run the system
    asyncio.run(main())