"use client";

import ApplicationsList from "@/components/ApplicationsList";
import BotControls from "@/components/BotControls";
import DashboardStats from "@/components/DashboardStats";
import JobsList from "@/components/JobsList";
import LogsViewer from "@/components/LogsViewer";
import ThemeToggle from "@/components/ThemeToggle";
import { API_ENDPOINTS } from "@/utils/constants";
import { useEffect, useState } from "react";
import { FiBriefcase, FiFileText, FiMail, FiPieChart } from "react-icons/fi";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.STATS);
      const data = await response.json();
      if (data.success) {
        setStats(data.data);
      }
    } catch (error) {
      console.error("Error fetching stats:", error);
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
    {
      id: "overview",
      name: "Visão Geral",
      icon: <FiPieChart className="mr-2" />,
    },
    { id: "jobs", name: "Vagas", icon: <FiBriefcase className="mr-2" /> },
    {
      id: "applications",
      name: "Candidaturas",
      icon: <FiMail className="mr-2" />,
    },
    { id: "logs", name: "Logs", icon: <FiFileText className="mr-2" /> },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  JobHunter Bot
                </h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <ThemeToggle />
              <BotControls onStatusChange={fetchStats} />
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center ${
                  activeTab === tab.id
                    ? "border-blue-500 text-blue-600 dark:text-blue-400"
                    : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600"
                }`}
              >
                {tab.icon}
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
              {activeTab === "overview" && <DashboardStats stats={stats} />}
              {activeTab === "jobs" && <JobsList />}
              {activeTab === "applications" && <ApplicationsList />}
              {activeTab === "logs" && <LogsViewer />}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
