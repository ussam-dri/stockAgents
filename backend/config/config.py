"""
Configuration management for the A2A Stock Management System
"""

import yaml
import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class OracleConfig:
    host: str
    port: int
    service_name: str
    username: str
    password: str
    min_connections: int = 2
    max_connections: int = 10

@dataclass
class EmailConfig:
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    from_email: str
    manager_emails: list
    use_tls: bool = True

@dataclass
class SupplierConfig:
    name: str
    location: str
    pricing_strategy: str
    catalog: Dict[str, Dict]

@dataclass
class InventoryConfig:
    check_interval: int = 60  # seconds
    thresholds: Dict[str, int] = None

@dataclass
class StockManagerConfig:
    offer_timeout: int = 300  # seconds
    selection_criteria: Dict[str, float] = None

@dataclass
class ManagerConfig:
    auto_approve_threshold: float = 1000.0

class Config:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self._load_config()
        
    def _load_config(self):
        """Load configuration from YAML file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        else:
            config_data = self._get_default_config()
            self._save_default_config(config_data)
            
        self._parse_config(config_data)
        
    def _parse_config(self, config_data: Dict[str, Any]):
        """Parse configuration data into structured objects"""
        # Oracle configuration
        oracle_config = config_data.get('oracle', {})
        self.oracle = OracleConfig(
            host=oracle_config.get('host', 'localhost'),
            port=oracle_config.get('port', 1521),
            service_name=oracle_config.get('service_name', 'ORCL'),
            username=oracle_config.get('username', 'inventory'),
            password=oracle_config.get('password', 'password'),
            min_connections=oracle_config.get('min_connections', 2),
            max_connections=oracle_config.get('max_connections', 10)
        )
        
        # Email configuration
        email_config = config_data.get('email', {})
        self.email = EmailConfig(
            smtp_server=email_config.get('smtp_server', 'smtp.gmail.com'),
            smtp_port=email_config.get('smtp_port', 587),
            username=email_config.get('username', ''),
            password=email_config.get('password', ''),
            from_email=email_config.get('from_email', 'system@company.com'),
            manager_emails=email_config.get('manager_emails', ['manager@company.com']),
            use_tls=email_config.get('use_tls', True)
        )
        
        # Supplier configurations
        suppliers_config = config_data.get('suppliers', {})
        self.suppliers = {}
        for supplier_id, supplier_data in suppliers_config.items():
            self.suppliers[supplier_id] = SupplierConfig(
                name=supplier_data.get('name', f'Supplier {supplier_id}'),
                location=supplier_data.get('location', 'Unknown'),
                pricing_strategy=supplier_data.get('pricing_strategy', 'standard'),
                catalog=supplier_data.get('catalog', {})
            )
            
        # Inventory configuration
        inventory_config = config_data.get('inventory', {})
        self.inventory = InventoryConfig(
            check_interval=inventory_config.get('check_interval', 60),
            thresholds=inventory_config.get('thresholds', {
                'WIDGET_A': 50,
                'COMP_B': 25,
                'MAT_C': 100,
                'TOOL_D': 20
            })
        )
        
        # Stock manager configuration
        stock_manager_config = config_data.get('stock_manager', {})
        self.stock_manager = StockManagerConfig(
            offer_timeout=stock_manager_config.get('offer_timeout', 300),
            selection_criteria=stock_manager_config.get('selection_criteria', {
                'price_weight': 0.4,
                'speed_weight': 0.3,
                'reliability_weight': 0.3
            })
        )
        
        # Manager configuration
        manager_config = config_data.get('manager', {})
        self.manager = ManagerConfig(
            auto_approve_threshold=manager_config.get('auto_approve_threshold', 1000.0)
        )
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'oracle': {
                'host': 'localhost',
                'port': 1521,
                'service_name': 'ORCL',
                'username': 'inventory',
                'password': 'password',
                'min_connections': 2,
                'max_connections': 10
            },
            'email': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': 'your_email@gmail.com',
                'password': 'your_app_password',
                'from_email': 'system@company.com',
                'manager_emails': ['manager@company.com'],
                'use_tls': True
            },
            'suppliers': {
                '1': {
                    'name': 'Supplier Alpha',
                    'location': 'US-East',
                    'pricing_strategy': 'competitive',
                    'catalog': {
                        'WIDGET_A': {'base_price': 10.50, 'min_order_quantity': 50},
                        'COMP_B': {'base_price': 2.75, 'min_order_quantity': 25},
                        'MAT_C': {'base_price': 1.25, 'min_order_quantity': 100},
                        'TOOL_D': {'base_price': 45.99, 'min_order_quantity': 10}
                    }
                },
                '2': {
                    'name': 'Supplier Beta',
                    'location': 'EU-West',
                    'pricing_strategy': 'premium',
                    'catalog': {
                        'WIDGET_A': {'base_price': 11.25, 'min_order_quantity': 40},
                        'COMP_B': {'base_price': 2.95, 'min_order_quantity': 20},
                        'MAT_C': {'base_price': 1.35, 'min_order_quantity': 80},
                        'TOOL_D': {'base_price': 48.50, 'min_order_quantity': 5}
                    }
                },
                '3': {
                    'name': 'Supplier Gamma',
                    'location': 'Asia-Pacific',
                    'pricing_strategy': 'standard',
                    'catalog': {
                        'WIDGET_A': {'base_price': 9.75, 'min_order_quantity': 60},
                        'COMP_B': {'base_price': 2.50, 'min_order_quantity': 30},
                        'MAT_C': {'base_price': 1.15, 'min_order_quantity': 120},
                        'TOOL_D': {'base_price': 42.99, 'min_order_quantity': 15}
                    }
                }
            },
            'inventory': {
                'check_interval': 60,
                'thresholds': {
                    'WIDGET_A': 50,
                    'COMP_B': 25,
                    'MAT_C': 100,
                    'TOOL_D': 20
                }
            },
            'stock_manager': {
                'offer_timeout': 300,
                'selection_criteria': {
                    'price_weight': 0.4,
                    'speed_weight': 0.3,
                    'reliability_weight': 0.3
                }
            },
            'manager': {
                'auto_approve_threshold': 1000.0
            }
        }
        
    def _save_default_config(self, config_data: Dict[str, Any]):
        """Save default configuration to file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)