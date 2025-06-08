"""
Google A2A Framework Implementation
Based on https://github.com/google-a2a/A2A
"""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import redis
import websockets

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    NOTIFICATION = "notification"

@dataclass
class AgentAddress:
    agent_id: str
    host: str = "localhost"
    port: int = 8000
    
    def __str__(self):
        return f"{self.agent_id}@{self.host}:{self.port}"

@dataclass
class Message:
    id: str
    sender: AgentAddress
    recipient: AgentAddress
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: str
    correlation_id: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        data['sender'] = AgentAddress(**data['sender'])
        data['recipient'] = AgentAddress(**data['recipient'])
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)

class A2ATransport(ABC):
    """Abstract transport layer for A2A communication"""
    
    @abstractmethod
    async def send_message(self, message: Message) -> bool:
        pass
    
    @abstractmethod
    async def receive_message(self) -> Optional[Message]:
        pass
    
    @abstractmethod
    async def subscribe(self, topic: str, callback: Callable):
        pass

class RedisTransport(A2ATransport):
    """Redis-based transport for A2A communication"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.subscriptions = {}
        self.logger = logging.getLogger(__name__)
    
    async def send_message(self, message: Message) -> bool:
        try:
            channel = f"agent:{message.recipient.agent_id}"
            # Convert message to dict and then serialize to JSON string
            message_dict = message.to_dict()
            message_data = json.dumps(message_dict)
            
            # Send to specific agent channel
            self.redis_client.publish(channel, message_data)
            
            # Store in message queue for reliability
            queue_key = f"queue:{message.recipient.agent_id}"
            self.redis_client.lpush(queue_key, message_data)
            
            self.logger.info(f"Message sent from {message.sender.agent_id} to {message.recipient.agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    async def receive_message(self, agent_id: str) -> Optional[Message]:
        try:
            queue_key = f"queue:{agent_id}"
            message_data = self.redis_client.rpop(queue_key)
            
            if message_data:
                message_dict = json.loads(message_data)
                return Message.from_dict(message_dict)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to receive message: {e}")
            return None
    
    async def subscribe(self, topic: str, callback: Callable):
        self.subscriptions[topic] = callback
        self.pubsub.subscribe(topic)
        
        # Start listening in background
        asyncio.create_task(self._listen_for_messages())
    
    async def _listen_for_messages(self):
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                topic = message['channel']
                if topic in self.subscriptions:
                    try:
                        message_dict = json.loads(message['data'])
                        msg = Message.from_dict(message_dict)
                        await self.subscriptions[topic](msg)
                    except Exception as e:
                        self.logger.error(f"Error processing message: {e}")

class A2AAgent(ABC):
    """Base class for A2A agents following Google's A2A patterns"""
    
    def __init__(self, agent_id: str, transport: A2ATransport, host: str = "localhost", port: int = 8000):
        self.address = AgentAddress(agent_id, host, port)
        self.transport = transport
        self.capabilities = {}
        self.state = "idle"
        self.message_handlers = {}
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self.running = False
    
    async def start(self):
        """Start the agent"""
        self.running = True
        self.state = "active"
        
        # Subscribe to agent's message channel
        await self.transport.subscribe(f"agent:{self.address.agent_id}", self._handle_incoming_message)
        
        # Start message processing loop
        asyncio.create_task(self._message_loop())
        
        self.logger.info(f"Agent {self.address.agent_id} started")
    
    async def stop(self):
        """Stop the agent"""
        self.running = False
        self.state = "stopped"
        self.logger.info(f"Agent {self.address.agent_id} stopped")
    
    async def send_message(self, recipient: AgentAddress, content: Dict[str, Any], 
                          message_type: MessageType = MessageType.REQUEST) -> str:
        """Send a message to another agent"""
        message_id = str(uuid.uuid4())
        message = Message(
            id=message_id,
            sender=self.address,
            recipient=recipient,
            message_type=message_type,
            content=content,
            timestamp=datetime.utcnow().isoformat()
        )
        
        success = await self.transport.send_message(message)
        if success:
            self.logger.info(f"Sent message {message_id} to {recipient.agent_id}")
        
        return message_id
    
    async def broadcast_message(self, content: Dict[str, Any], topic: str = "broadcast"):
        """Broadcast a message to all agents"""
        broadcast_address = AgentAddress("broadcast", "localhost", 0)
        await self.send_message(broadcast_address, content, MessageType.BROADCAST)
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler"""
        self.message_handlers[message_type] = handler
    
    async def _handle_incoming_message(self, message: Message):
        """Handle incoming messages"""
        try:
            content_type = message.content.get('type', 'unknown')
            
            if content_type in self.message_handlers:
                await self.message_handlers[content_type](message)
            else:
                await self.handle_message(message)
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _message_loop(self):
        """Main message processing loop"""
        while self.running:
            try:
                message = await self.transport.receive_message(self.address.agent_id)
                if message:
                    await self._handle_incoming_message(message)
                else:
                    await asyncio.sleep(0.1)  # Prevent busy waiting
                    
            except Exception as e:
                self.logger.error(f"Error in message loop: {e}")
                await asyncio.sleep(1)
    
    @abstractmethod
    async def handle_message(self, message: Message):
        """Handle incoming messages - to be implemented by subclasses"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.address.agent_id,
            'state': self.state,
            'capabilities': self.capabilities,
            'timestamp': datetime.utcnow().isoformat()
        }

class A2ARegistry:
    """Agent registry for service discovery"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)
    
    async def register_agent(self, agent: A2AAgent):
        """Register an agent in the registry"""
        key = f"registry:agent:{agent.address.agent_id}"
        
        # Set each field individually
        self.redis_client.hset(key, 'agent_id', agent.address.agent_id)
        self.redis_client.hset(key, 'host', agent.address.host)
        self.redis_client.hset(key, 'port', str(agent.address.port))  # Convert port to string
        self.redis_client.hset(key, 'capabilities', json.dumps(agent.capabilities))
        self.redis_client.hset(key, 'state', agent.state)
        self.redis_client.hset(key, 'registered_at', datetime.utcnow().isoformat())
        
        self.redis_client.expire(key, 300)  # 5 minute TTL
        
        self.logger.info(f"Registered agent {agent.address.agent_id}")
    
    async def discover_agents(self, capability: str = None) -> List[Dict]:
        """Discover agents by capability"""
        pattern = "registry:agent:*"
        agents = []
        
        for key in self.redis_client.scan_iter(match=pattern):
            agent_info = self.redis_client.hgetall(key)
            
            if capability:
                # Parse the JSON string back to dictionary
                agent_capabilities = json.loads(agent_info.get('capabilities', '{}'))
                if capability in agent_capabilities:
                    # Convert capabilities back to dict for the response
                    agent_info['capabilities'] = agent_capabilities
                    agents.append(agent_info)
            else:
                # Convert capabilities back to dict for the response
                agent_info['capabilities'] = json.loads(agent_info.get('capabilities', '{}'))
                agents.append(agent_info)
        
        return agents
    
    async def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get specific agent information"""
        key = f"registry:agent:{agent_id}"
        agent_info = self.redis_client.hgetall(key)
        return agent_info if agent_info else None

class A2ASystem:
    """Main A2A system class that manages agents and system state"""
    
    _instance = None
    
    def __init__(self):
        self.agents = []
        self.transport = None
        self.registry = None
        self.database = None
        self.llm = None
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of A2ASystem"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def initialize(self, config):
        """Initialize the A2A system with configuration"""
        try:
            # Initialize Redis transport
            self.transport = RedisTransport(config.redis.url)
            
            # Initialize Redis registry
            redis_client = redis.from_url(config.redis.url, decode_responses=True)
            self.registry = A2ARegistry(redis_client)
            
            # Initialize database connection
            self.database = config.database
            
            # Initialize LLM service if configured
            if hasattr(config, 'llm') and config.llm.api_key:
                self.llm = config.llm
            
            self.logger.info("A2A System initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize A2A System: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Check if the system is properly connected"""
        return (
            self.transport is not None and
            self.registry is not None and
            self.database is not None
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'total_agents': len(self.agents),
            'database_connected': self.database is not None,
            'llm_enabled': self.llm is not None,
            'transport_type': self.transport.__class__.__name__ if self.transport else None,
            'timestamp': datetime.utcnow().isoformat()
        }