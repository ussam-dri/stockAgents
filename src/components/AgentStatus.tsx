import React from 'react';
import { Bot, MapPin, Clock, Activity } from 'lucide-react';
import { Agent } from '../types';

interface AgentStatusProps {
  agents: Agent[];
}

const AgentStatus: React.FC<AgentStatusProps> = ({ agents }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800 border-green-200';
      case 'busy': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'idle': return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'error': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getAgentIcon = (type: string) => {
    return <Bot className="w-5 h-5" />;
  };

  const formatLastActivity = (timestamp: string) => {
    const now = new Date();
    const activity = new Date(timestamp);
    const diffMs = now.getTime() - activity.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center">
          <Activity className="w-6 h-6 mr-2 text-blue-600" />
          Agent Status
        </h2>
      </div>
      
      <div className="p-6">
        <div className="space-y-4">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow duration-200"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-50 rounded-lg">
                    {getAgentIcon(agent.type)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                    <p className="text-sm text-gray-500 capitalize">{agent.type.replace('_', ' ')}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(agent.status)}`}>
                  {agent.status}
                </span>
              </div>
              
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4" />
                  <span>Last active: {formatLastActivity(agent.lastActivity)}</span>
                </div>
                {agent.location && (
                  <div className="flex items-center space-x-2">
                    <MapPin className="w-4 h-4" />
                    <span>Location: {agent.location}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AgentStatus;