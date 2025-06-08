import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import Header from './components/Header';
import { mockData } from './data/mockData';
import { SystemData } from './types';

function App() {
  const [systemData, setSystemData] = useState<SystemData>(mockData);
  const [isConnected, setIsConnected] = useState(false);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemData(prevData => ({
        ...prevData,
        lastUpdate: new Date().toISOString(),
        inventory: prevData.inventory.map(item => ({
          ...item,
          currentStock: Math.max(0, item.currentStock + Math.floor(Math.random() * 3) - 1)
        }))
      }));
    }, 5000);

    // Simulate connection status
    setTimeout(() => setIsConnected(true), 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header isConnected={isConnected} />
      <main className="container mx-auto px-4 py-6">
        <Dashboard data={systemData} />
      </main>
    </div>
  );
}

export default App;