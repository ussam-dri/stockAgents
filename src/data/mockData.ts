import { SystemData } from '../types';

export const mockData: SystemData = {
  inventory: [
    {
      id: '1',
      name: 'Widget A',
      currentStock: 45,
      threshold: 50,
      unit: 'units',
      category: 'Electronics'
    },
    {
      id: '2',
      name: 'Component B',
      currentStock: 12,
      threshold: 25,
      unit: 'units',
      category: 'Parts'
    },
    {
      id: '3',
      name: 'Material C',
      currentStock: 78,
      threshold: 100,
      unit: 'kg',
      category: 'Raw Materials'
    },
    {
      id: '4',
      name: 'Tool D',
      currentStock: 5,
      threshold: 20,
      unit: 'units',
      category: 'Tools'
    }
  ],
  agents: [
    {
      id: 'inv-001',
      name: 'Inventory Agent',
      type: 'inventory',
      status: 'active',
      lastActivity: new Date(Date.now() - 30000).toISOString()
    },
    {
      id: 'sup-001',
      name: 'Supplier Agent Alpha',
      type: 'supplier',
      status: 'active',
      lastActivity: new Date(Date.now() - 120000).toISOString(),
      location: 'US-East'
    },
    {
      id: 'sup-002',
      name: 'Supplier Agent Beta',
      type: 'supplier',
      status: 'busy',
      lastActivity: new Date(Date.now() - 60000).toISOString(),
      location: 'EU-West'
    },
    {
      id: 'sup-003',
      name: 'Supplier Agent Gamma',
      type: 'supplier',
      status: 'idle',
      lastActivity: new Date(Date.now() - 300000).toISOString(),
      location: 'Asia-Pacific'
    },
    {
      id: 'mgr-001',
      name: 'Stock Manager Agent',
      type: 'stock_manager',
      status: 'active',
      lastActivity: new Date(Date.now() - 45000).toISOString()
    },
    {
      id: 'mgr-002',
      name: 'Manager Agent',
      type: 'manager',
      status: 'idle',
      lastActivity: new Date(Date.now() - 180000).toISOString()
    }
  ],
  offers: [
    {
      id: 'offer-001',
      supplierId: 'sup-001',
      supplierName: 'Supplier Alpha',
      productId: '2',
      quantity: 50,
      price: 125.50,
      deliveryTime: 2,
      timestamp: new Date(Date.now() - 300000).toISOString(),
      status: 'selected'
    },
    {
      id: 'offer-002',
      supplierId: 'sup-002',
      supplierName: 'Supplier Beta',
      productId: '2',
      quantity: 50,
      price: 135.75,
      deliveryTime: 1,
      timestamp: new Date(Date.now() - 280000).toISOString(),
      status: 'rejected'
    },
    {
      id: 'offer-003',
      supplierId: 'sup-003',
      supplierName: 'Supplier Gamma',
      productId: '4',
      quantity: 25,
      price: 89.99,
      deliveryTime: 3,
      timestamp: new Date(Date.now() - 120000).toISOString(),
      status: 'pending'
    }
  ],
  logs: [
    {
      id: 'log-001',
      timestamp: new Date(Date.now() - 60000).toISOString(),
      level: 'warning',
      message: 'Component B stock below threshold (12/25 units)',
      agentId: 'inv-001'
    },
    {
      id: 'log-002',
      timestamp: new Date(Date.now() - 120000).toISOString(),
      level: 'info',
      message: 'Supplier offers received for Component B',
      agentId: 'mgr-001'
    },
    {
      id: 'log-003',
      timestamp: new Date(Date.now() - 180000).toISOString(),
      level: 'success',
      message: 'Best offer selected: Supplier Alpha - $125.50',
      agentId: 'mgr-001'
    },
    {
      id: 'log-004',
      timestamp: new Date(Date.now() - 240000).toISOString(),
      level: 'error',
      message: 'Tool D critically low stock (5/20 units)',
      agentId: 'inv-001'
    },
    {
      id: 'log-005',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      level: 'info',
      message: 'System initialization complete',
      agentId: 'system'
    }
  ],
  lastUpdate: new Date().toISOString(),
  systemStatus: 'running'
};