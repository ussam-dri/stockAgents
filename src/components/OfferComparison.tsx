import React from 'react';
import { DollarSign, Clock, Package, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { SupplierOffer, InventoryItem } from '../types';

interface OfferComparisonProps {
  offers: SupplierOffer[];
  inventory: InventoryItem[];
}

const OfferComparison: React.FC<OfferComparisonProps> = ({ offers, inventory }) => {
  const getProductName = (productId: string) => {
    const product = inventory.find(item => item.id === productId);
    return product?.name || `Product ${productId}`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'selected': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'rejected': return <XCircle className="w-5 h-5 text-red-500" />;
      case 'pending': return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'selected': return 'bg-green-50 border-green-200';
      case 'rejected': return 'bg-red-50 border-red-200';
      case 'pending': return 'bg-yellow-50 border-yellow-200';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center">
          <DollarSign className="w-6 h-6 mr-2 text-blue-600" />
          Supplier Offers
        </h2>
      </div>
      
      <div className="p-6">
        {offers.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Package className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No supplier offers available</p>
          </div>
        ) : (
          <div className="space-y-4">
            {offers.map((offer) => (
              <div
                key={offer.id}
                className={`p-4 border-2 rounded-lg transition-all duration-200 hover:shadow-md ${getStatusColor(offer.status)}`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(offer.status)}
                    <div>
                      <h3 className="font-semibold text-gray-900">{offer.supplierName}</h3>
                      <p className="text-sm text-gray-600">{getProductName(offer.productId)}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full capitalize ${
                    offer.status === 'selected' ? 'bg-green-100 text-green-800' :
                    offer.status === 'rejected' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {offer.status}
                  </span>
                </div>
                
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="text-center p-2 bg-white rounded">
                    <div className="flex items-center justify-center mb-1">
                      <Package className="w-4 h-4 text-gray-400 mr-1" />
                      <span className="text-gray-600">Quantity</span>
                    </div>
                    <span className="font-semibold">{offer.quantity} units</span>
                  </div>
                  
                  <div className="text-center p-2 bg-white rounded">
                    <div className="flex items-center justify-center mb-1">
                      <DollarSign className="w-4 h-4 text-gray-400 mr-1" />
                      <span className="text-gray-600">Price</span>
                    </div>
                    <span className="font-semibold">${offer.price.toFixed(2)}</span>
                  </div>
                  
                  <div className="text-center p-2 bg-white rounded">
                    <div className="flex items-center justify-center mb-1">
                      <Clock className="w-4 h-4 text-gray-400 mr-1" />
                      <span className="text-gray-600">Delivery</span>
                    </div>
                    <span className="font-semibold">{offer.deliveryTime} days</span>
                  </div>
                </div>
                
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    Received: {new Date(offer.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OfferComparison;