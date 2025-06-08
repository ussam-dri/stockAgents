"""
Main entry point for the A2A Stock Management System with Gemini LLM
"""

import asyncio
import logging
import signal
import sys
import os
from typing import List
from flask import Flask
from flask_cors import CORS
from api.routes import api
from database.oracle_connection import OracleConnection
from core.a2a_framework import A2ASystem

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.a2a_framework import RedisTransport, A2ARegistry
from core.gemini_integration import GeminiLLMService
from agents.inventory_agent import InventoryAgent
from agents.supplier_agent import SupplierAgent
from agents.stock_manager_agent import StockManagerAgent
from agents.manager_agent import ManagerAgent
from config.config import Config
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global variables for shared resources
db = None
system = None

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    
    # Register API routes
    app.register_blueprint(api)
    
    # Initialize A2A System
    try:
        global system
        system = A2ASystem.get_instance()
        logger.info("A2A Stock Management System initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize A2A System: {str(e)}")
        raise
    
    return app

async def init_database():
    """Initialize the Oracle database connection"""
    try:
        global db
        db = OracleConnection(Config().oracle.__dict__)
        await db.initialize()
        await db.create_tables()
        logger.info("Oracle database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Oracle database: {str(e)}")
        raise

async def cleanup():
    """Cleanup resources before shutdown"""
    try:
        if db:
            await db.close()
            logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cleanup())
    sys.exit(0)

if __name__ == '__main__':
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Initialize database
        loop.run_until_complete(init_database())
        
        # Create and run Flask app
        app = create_app()
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        loop.run_until_complete(cleanup())
        sys.exit(1)
    finally:
        loop.close()