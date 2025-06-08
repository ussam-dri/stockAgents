import React from 'react';
import { FileText, AlertCircle, Info, CheckCircle, XCircle } from 'lucide-react';
import { SystemLog } from '../types';

interface SystemLogsProps {
  logs: SystemLog[];
}

const SystemLogs: React.FC<SystemLogsProps> = ({ logs }) => {
  const getLogIcon = (level: string) => {
    switch (level) {
      case 'error': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'success': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'info': return <Info className="w-4 h-4 text-blue-500" />;
    }
  };

  const getLogColor = (level: string) => {
    switch (level) {
      case 'error': return 'border-l-red-400 bg-red-50';
      case 'warning': return 'border-l-yellow-400 bg-yellow-50';
      case 'success': return 'border-l-green-400 bg-green-50';
      case 'info': return 'border-l-blue-400 bg-blue-50';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center">
          <FileText className="w-6 h-6 mr-2 text-blue-600" />
          System Logs
        </h2>
      </div>
      
      <div className="p-6">
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {logs.map((log) => (
            <div
              key={log.id}
              className={`p-3 border-l-4 rounded-r-lg ${getLogColor(log.level)}`}
            >
              <div className="flex items-start space-x-3">
                {getLogIcon(log.level)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">{log.message}</p>
                  <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                    <span>{formatTimestamp(log.timestamp)}</span>
                    {log.agentId && (
                      <span className="px-2 py-1 bg-white rounded font-medium">
                        {log.agentId}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SystemLogs;