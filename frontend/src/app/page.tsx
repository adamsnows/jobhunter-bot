'use client';

import { useState, useEffect } from 'react';
import DashboardStats from '@/components/DashboardStats';
import BotControls from '@/components/BotControls';
import JobsList from '@/components/JobsList';
import ApplicationsList from '@/components/ApplicationsList';
import LogsViewer from '@/components/LogsViewer';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/stats');
      const data = await response.json();
      if (data.success) {
        setStats(data.data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Atualiza a cada 30s
    return () => clearInterval(interval);
  }, []);

  const tabs = [
    { id: 'overview', name: 'Visão Geral', icon: '📊' },
    { id: 'jobs', name: 'Vagas', icon: '💼' },
    { id: 'applications', name: 'Candidaturas', icon: '📧' },
    { id: 'logs', name: 'Logs', icon: '📝' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-gray-900">
                  🤖 JobHunter Bot
                </h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <BotControls onStatusChange={fetchStats} />
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
            </div>
          ) : (
            <>
              {activeTab === 'overview' && <DashboardStats stats={stats} />}
              {activeTab === 'jobs' && <JobsList />}
              {activeTab === 'applications' && <ApplicationsList />}
              {activeTab === 'logs' && <LogsViewer />}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
