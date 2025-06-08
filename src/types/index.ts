export interface InventoryItem {
  id: string;
  name: string;
  currentStock: number;
  threshold: number;
  unit: string;
  category: string;
}

export interface Agent {
  id: string;
  name: string;
  type: 'inventory' | 'supplier' | 'manager' | 'stock_manager';
  status: 'active' | 'idle' | 'busy' | 'error';
  lastActivity: string;
  location?: string;
}

export interface SupplierOffer {
  id: string;
  supplierId: string;
  supplierName: string;
  productId: string;
  quantity: number;
  price: number;
  deliveryTime: number;
  timestamp: string;
  status: 'pending' | 'selected' | 'rejected';
}

export interface SystemLog {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  agentId?: string;
}

export interface SystemData {
  inventory: InventoryItem[];
  agents: Agent[];
  offers: SupplierOffer[];
  logs: SystemLog[];
  lastUpdate: string;
  systemStatus: 'running' | 'stopped' | 'error';
}