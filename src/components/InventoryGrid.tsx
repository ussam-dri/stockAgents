import React from 'react';
import { Package, AlertTriangle, TrendingDown, CheckCircle } from 'lucide-react';
import { InventoryItem } from '../types';

interface InventoryGridProps {
  inventory: InventoryItem[];
}

const InventoryGrid: React.FC<InventoryGridProps> = ({ inventory }) => {
  const getStockStatus = (item: InventoryItem) => {
    const percentage = (item.currentStock / item.threshold) * 100;
    if (percentage <= 25) return 'critical';
    if (percentage <= 50) return 'low';
    if (percentage <= 75) return 'medium';
    return 'good';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical': return 'bg-red-50 border-red-200 text-red-800';
      case 'low': return 'bg-orange-50 border-orange-200 text-orange-800';
      case 'medium': return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'good': return 'bg-green-50 border-green-200 text-green-800';
      default: return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'critical': return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'low': return <TrendingDown className="w-5 h-5 text-orange-500" />;
      case 'medium': return <Package className="w-5 h-5 text-yellow-500" />;
      case 'good': return <CheckCircle className="w-5 h-5 text-green-500" />;
      default: return <Package className="w-5 h-5 text-gray-500" />;
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center">
          <Package className="w-6 h-6 mr-2 text-blue-600" />
          Inventory Status
        </h2>
      </div>
      
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {inventory.map((item) => {
            const status = getStockStatus(item);
            const percentage = (item.currentStock / item.threshold) * 100;
            
            return (
              <div
                key={item.id}
                className={`p-4 rounded-lg border-2 transition-all duration-200 hover:shadow-md ${getStatusColor(status)}`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(status)}
                    <h3 className="font-semibold">{item.name}</h3>
                  </div>
                  <span className="text-xs px-2 py-1 bg-white rounded-full font-medium">
                    {item.category}
                  </span>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Current Stock:</span>
                    <span className="font-semibold">{item.currentStock} {item.unit}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Threshold:</span>
                    <span>{item.threshold} {item.unit}</span>
                  </div>
                  
                  <div className="mt-3">
                    <div className="flex justify-between text-xs mb-1">
                      <span>Stock Level</span>
                      <span>{percentage.toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-white rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          status === 'critical' ? 'bg-red-400' :
                          status === 'low' ? 'bg-orange-400' :
                          status === 'medium' ? 'bg-yellow-400' : 'bg-green-400'
                        }`}
                        style={{ width: `${Math.min(percentage, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default InventoryGrid;