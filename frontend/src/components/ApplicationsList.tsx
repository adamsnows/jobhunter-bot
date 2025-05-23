"use client";

import { API_ENDPOINTS } from "@/utils/constants";
import { useEffect, useState } from "react";

interface Application {
  id: number;
  job_id: number;
  job_title: string;
  company: string;
  applied_at: string;
  status: "pending" | "applied" | "rejected" | "interview" | "accepted";
  platform: string;
  application_url?: string;
}

export default function ApplicationsList() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  const fetchApplications = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.APPLICATIONS);
      const data = await response.json();
      if (data.success) {
        setApplications(data.data);
      }
    } catch (error) {
      console.error("Error fetching applications:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      case "applied":
        return "bg-blue-100 text-blue-800";
      case "rejected":
        return "bg-red-100 text-red-800";
      case "interview":
        return "bg-purple-100 text-purple-800";
      case "accepted":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pending":
        return "⏳";
      case "applied":
        return "📧";
      case "rejected":
        return "❌";
      case "interview":
        return "🗣️";
      case "accepted":
        return "✅";
      default:
        return "❓";
    }
  };

  const filteredApplications = applications.filter(
    (app) => filter === "all" || app.status === filter
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
      {/* Header com filtros */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">
          📧 Candidaturas Enviadas
        </h2>
        <div className="flex space-x-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">Todas</option>
            <option value="pending">Pendentes</option>
            <option value="applied">Enviadas</option>
            <option value="interview">Entrevista</option>
            <option value="accepted">Aceitas</option>
            <option value="rejected">Rejeitadas</option>
          </select>
          <button
            onClick={fetchApplications}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            🔄 Atualizar
          </button>
        </div>
      </div>

      {/* Lista de candidaturas */}
      {filteredApplications.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📭</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Nenhuma candidatura encontrada
          </h3>
          <p className="text-gray-500">
            {filter === "all"
              ? "O bot ainda não enviou nenhuma candidatura."
              : `Nenhuma candidatura com status "${filter}".`}
          </p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {filteredApplications.map((application) => (
              <li key={application.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                          <span className="text-blue-600 font-semibold">
                            {application.company.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="flex items-center">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {application.job_title}
                          </p>
                          <span className="ml-2 text-xs text-gray-500">
                            #{application.job_id}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center text-sm text-gray-500">
                          <span className="mr-2">🏢</span>
                          <p className="truncate">{application.company}</p>
                          <span className="mx-2">•</span>
                          <span className="mr-1">📱</span>
                          <p>{application.platform}</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                          application.status
                        )}`}
                      >
                        <span className="mr-1">
                          {getStatusIcon(application.status)}
                        </span>
                        {application.status.charAt(0).toUpperCase() +
                          application.status.slice(1)}
                      </span>
                      <div className="text-sm text-gray-500">
                        {new Date(application.applied_at).toLocaleDateString(
                          "pt-BR"
                        )}
                      </div>
                    </div>
                  </div>

                  {application.application_url && (
                    <div className="mt-2">
                      <a
                        href={application.application_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 text-sm"
                      >
                        🔗 Ver candidatura
                      </a>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Estatísticas rápidas */}
      {applications.length > 0 && (
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              📊 Resumo de Candidaturas
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {["pending", "applied", "interview", "accepted", "rejected"].map(
                (status) => {
                  const count = applications.filter(
                    (app) => app.status === status
                  ).length;
                  return (
                    <div key={status} className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {count}
                      </div>
                      <div className="text-sm text-gray-500 capitalize">
                        {getStatusIcon(status)} {status}
                      </div>
                    </div>
                  );
                }
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
