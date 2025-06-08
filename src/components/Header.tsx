import React from 'react';
import { Activity, Database, Shield, AlertCircle } from 'lucide-react';

interface HeaderProps {
  isConnected: boolean;
}

const Header: React.FC<HeaderProps> = ({ isConnected }) => {
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-600 rounded-lg">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">A2A Stock Management</h1>
              <p className="text-sm text-gray-500">Multi-Agent Inventory System</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <Database className="w-5 h-5 text-gray-400" />
              <span className="text-sm text-gray-600">Oracle DB</span>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            </div>
            
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-gray-400" />
              <span className="text-sm text-gray-600">A2A Framework</span>
              <div className="w-2 h-2 rounded-full bg-green-500" />
            </div>
            
            <div className="flex items-center space-x-2 px-3 py-1 bg-green-50 rounded-full">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium text-green-700">System Running</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;