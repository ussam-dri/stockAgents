import axios from 'axios';

const API_BASE_URL ='http://localhost:5000';

export interface StockItem {
    product_id: string;
    product_name: string;
    category: string;
    current_stock: number;
    available_stock: number;
    unit: string;
    last_updated: string;
}

export interface AgentStatus {
    agent_id: string;
    state: string;
    capabilities: Record<string, boolean>;
    timestamp: string;
}

export interface SystemStatus {
    total_agents: number;
    database_connected: boolean;
    llm_enabled: boolean;
    transport_type: string;
}

class StockService {
    async getCurrentStock(): Promise<StockItem[]> {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/stock/current`);
            return response.data;
        } catch (error) {
            console.error('Error fetching current stock:', error);
            throw error;
        }
    }

    async getLowStockItems(): Promise<StockItem[]> {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/stock/low`);
            return response.data;
        } catch (error) {
            console.error('Error fetching low stock items:', error);
            throw error;
        }
    }

    async getSystemStatus(): Promise<SystemStatus> {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/system/status`);
            return response.data;
        } catch (error) {
            console.error('Error fetching system status:', error);
            throw error;
        }
    }

    async updateStock(productId: string, quantity: number): Promise<StockItem> {
        try {
            const response = await axios.put(`${API_BASE_URL}/api/stock/${productId}`, {
                quantity
            });
            return response.data;
        } catch (error) {
            console.error('Error updating stock:', error);
            throw error;
        }
    }

    async addStockItem(item: Omit<StockItem, 'product_id' | 'last_updated'>): Promise<StockItem> {
        try {
            const response = await axios.post(`${API_BASE_URL}/api/stock`, item);
            return response.data;
        } catch (error) {
            console.error('Error adding stock item:', error);
            throw error;
        }
    }

    async deleteStockItem(productId: string): Promise<void> {
        try {
            await axios.delete(`${API_BASE_URL}/api/stock/${productId}`);
        } catch (error) {
            console.error('Error deleting stock item:', error);
            throw error;
        }
    }

    async getAgentStatus(agentId: string): Promise<AgentStatus> {
        const response = await axios.get(`${API_BASE_URL}/api/agents/${agentId}/status`);
        return response.data;
    }
}

export const stockService = new StockService(); 