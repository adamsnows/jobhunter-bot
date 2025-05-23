'use client';

import { useState, useEffect } from 'react';

interface LogEntry {
  id: number;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  component?: string;
  details?: string;
}

export default function LogsViewer() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchLogs = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/logs');
      const data = await response.json();
      if (data.success) {
        setLogs(data.data);
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(fetchLogs, 5000); // Atualiza a cada 5s
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [autoRefresh]);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'info':
        return 'bg-blue-100 text-blue-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'success':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'info':
        return 'ℹ️';
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      case 'success':
        return '✅';
      default:
        return '📝';
    }
  };

  const clearLogs = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/logs', {
        method: 'DELETE',
      });
      const data = await response.json();
      if (data.success) {
        setLogs([]);
        alert('🗑️ Logs limpos com sucesso!');
      }
    } catch (error) {
      console.error('Error clearing logs:', error);
      alert('❌ Erro ao limpar logs');
    }
  };

  const filteredLogs = logs.filter(log => 
    filter === 'all' || log.level === filter
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header com controles */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">
          📝 Logs do Sistema
        </h2>
        <div className="flex items-center space-x-4">
          {/* Auto-refresh toggle */}
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
            />
            <span className="ml-2 text-sm text-gray-700">Auto-atualizar</span>
          </label>

          {/* Filtro por nível */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">Todos</option>
            <option value="info">Info</option>
            <option value="success">Sucesso</option>
            <option value="warning">Aviso</option>
            <option value="error">Erro</option>
          </select>

          {/* Botões de ação */}
          <button
            onClick={fetchLogs}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            🔄 Atualizar
          </button>
          
          <button
            onClick={clearLogs}
            className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50"
          >
            🗑️ Limpar
          </button>
        </div>
      </div>

      {/* Contador de logs */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{filteredLogs.length}</div>
              <div className="text-sm text-gray-500">
                {filter === 'all' ? 'Total' : filter.charAt(0).toUpperCase() + filter.slice(1)}
              </div>
            </div>
            {filter === 'all' && (
              <>
                {['info', 'success', 'warning', 'error'].map((level) => {
                  const count = logs.filter(log => log.level === level).length;
                  return (
                    <div key={level} className="text-center">
                      <div className="text-lg font-semibold text-gray-900">{count}</div>
                      <div className="text-xs text-gray-500">
                        {getLevelIcon(level)} {level}
                      </div>
                    </div>
                  );
                })}
              </>
            )}
          </div>
          {autoRefresh && (
            <div className="flex items-center text-sm text-gray-500">
              <div className="animate-pulse w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              Atualizando automaticamente
            </div>
          )}
        </div>
      </div>

      {/* Lista de logs */}
      {filteredLogs.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Nenhum log encontrado
          </h3>
          <p className="text-gray-500">
            {filter === 'all' 
              ? 'Nenhum log foi registrado ainda.'
              : `Nenhum log do tipo "${filter}".`
            }
          </p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="max-h-96 overflow-y-auto">
            <ul className="divide-y divide-gray-200">
              {filteredLogs.map((log) => (
                <li key={log.id} className="px-4 py-4 sm:px-6">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLevelColor(log.level)}`}>
                        {getLevelIcon(log.level)} {log.level.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-gray-900">
                          {log.message}
                        </p>
                        <div className="flex items-center text-sm text-gray-500">
                          {log.component && (
                            <>
                              <span className="mr-2">[{log.component}]</span>
                            </>
                          )}
                          <time dateTime={log.timestamp}>
                            {new Date(log.timestamp).toLocaleString('pt-BR')}
                          </time>
                        </div>
                      </div>
                      {log.details && (
                        <div className="mt-2 text-sm text-gray-600 bg-gray-50 p-2 rounded">
                          <pre className="whitespace-pre-wrap font-mono text-xs">
                            {log.details}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Scroll para o final */}
      {filteredLogs.length > 0 && (
        <div className="text-center">
          <button
            onClick={() => {
              const element = document.querySelector('.max-h-96');
              if (element) {
                element.scrollTop = element.scrollHeight;
              }
            }}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            ⬇️ Ir para o final
          </button>
        </div>
      )}
    </div>
  );
}
