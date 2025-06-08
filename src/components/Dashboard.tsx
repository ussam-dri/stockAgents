import React, { useEffect, useState } from 'react';
import InventoryGrid from './InventoryGrid';
import AgentStatus from './AgentStatus';
import OfferComparison from './OfferComparison';
import SystemLogs from './SystemLogs';
import { SystemData } from '../types';
import { stockService, StockItem, SystemStatus } from '../services/stockService';

interface DashboardProps {
  data: SystemData;
}

export default function Dashboard() {
    const [currentStock, setCurrentStock] = useState<StockItem[]>([]);
    const [lowStock, setLowStock] = useState<StockItem[]>([]);
    const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [stockData, lowStockData, statusData] = await Promise.all([
                    stockService.getCurrentStock(),
                    stockService.getLowStockItems(),
                    stockService.getSystemStatus()
                ]);
                setCurrentStock(stockData);
                setLowStock(lowStockData);
                setSystemStatus(statusData);
            } catch (err) {
                setError('Failed to fetch data. Please try again later.');
                console.error('Error fetching data:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return <div className="flex justify-center items-center h-screen">Loading...</div>;
    }

    if (error) {
        return <div className="text-red-500 text-center p-4">{error}</div>;
    }

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-3xl font-bold mb-6">Stock Management Dashboard</h1>
            
            {/* System Status */}
            {systemStatus && (
                <div className="bg-white rounded-lg shadow p-4 mb-6">
                    <h2 className="text-xl font-semibold mb-4">System Status</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="p-3 bg-gray-50 rounded">
                            <p className="text-sm text-gray-600">Total Agents</p>
                            <p className="text-lg font-semibold">{systemStatus.total_agents}</p>
                        </div>
                        <div className="p-3 bg-gray-50 rounded">
                            <p className="text-sm text-gray-600">Database Status</p>
                            <p className="text-lg font-semibold">
                                {systemStatus.database_connected ? 'Connected' : 'Disconnected'}
                            </p>
                        </div>
                        <div className="p-3 bg-gray-50 rounded">
                            <p className="text-sm text-gray-600">LLM Status</p>
                            <p className="text-lg font-semibold">
                                {systemStatus.llm_enabled ? 'Enabled' : 'Disabled'}
                            </p>
                        </div>
                        <div className="p-3 bg-gray-50 rounded">
                            <p className="text-sm text-gray-600">Transport</p>
                            <p className="text-lg font-semibold">{systemStatus.transport_type}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Low Stock Alert */}
            {lowStock.length > 0 && (
                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                    <div className="flex">
                        <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div className="ml-3">
                            <p className="text-sm text-yellow-700">
                                {lowStock.length} items are running low on stock
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Current Stock Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="px-4 py-5 sm:px-6">
                    <h2 className="text-xl font-semibold">Current Stock Levels</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Stock</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Available</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Updated</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {currentStock.map((item) => (
                                <tr key={item.product_id} className={item.current_stock <= 10 ? 'bg-red-50' : ''}>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900">{item.product_name}</div>
                                        <div className="text-sm text-gray-500">{item.product_id}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.category}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-gray-900">{item.current_stock}</div>
                                        <div className="text-sm text-gray-500">{item.unit}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.available_stock}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(item.last_updated).toLocaleString()}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}