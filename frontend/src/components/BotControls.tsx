'use client';

import { useState, useEffect } from 'react';

interface BotControlsProps {
  onStatusChange: () => void;
}

export default function BotControls({ onStatusChange }: BotControlsProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const checkStatus = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/daemon/status');
      const data = await response.json();
      if (data.success) {
        setIsRunning(data.data.running);
        setLastUpdate(new Date().toLocaleTimeString());
      }
    } catch (error) {
      console.error('Error checking status:', error);
      setIsRunning(false);
    }
  };

  const startBot = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/daemon/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      
      if (data.success) {
        setIsRunning(true);
        onStatusChange();
        alert('✅ Bot iniciado com sucesso!');
      } else {
        alert(`❌ Erro ao iniciar: ${data.message || data.error}`);
      }
    } catch (error) {
      console.error('Error starting bot:', error);
      alert('❌ Erro ao conectar com o servidor');
    } finally {
      setLoading(false);
    }
  };

  const stopBot = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/daemon/stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      
      if (data.success) {
        setIsRunning(false);
        onStatusChange();
        alert('🛑 Bot parado com sucesso!');
      } else {
        alert(`❌ Erro ao parar: ${data.message || data.error}`);
      }
    } catch (error) {
      console.error('Error stopping bot:', error);
      alert('❌ Erro ao conectar com o servidor');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 10000); // Verifica a cada 10s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center space-x-4">
      {/* Status Indicator */}
      <div className="flex items-center space-x-2">
        <div className={`w-3 h-3 rounded-full ${
          isRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'
        }`}></div>
        <span className={`text-sm font-medium ${
          isRunning ? 'text-green-700' : 'text-red-700'
        }`}>
          {isRunning ? 'Ativo' : 'Parado'}
        </span>
      </div>

      {/* Last Update */}
      {lastUpdate && (
        <span className="text-xs text-gray-500">
          Última atualização: {lastUpdate}
        </span>
      )}

      {/* Control Buttons */}
      <div className="flex space-x-2">
        {!isRunning ? (
          <button
            onClick={startBot}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            ) : (
              <span className="mr-2">▶️</span>
            )}
            {loading ? 'Iniciando...' : 'Iniciar Bot'}
          </button>
        ) : (
          <button
            onClick={stopBot}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            ) : (
              <span className="mr-2">⏹️</span>
            )}
            {loading ? 'Parando...' : 'Parar Bot'}
          </button>
        )}
        
        <button
          onClick={checkStatus}
          disabled={loading}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <span className="mr-1">🔄</span>
          Atualizar
        </button>
      </div>
    </div>
  );
}
