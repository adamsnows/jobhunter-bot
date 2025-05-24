"use client";

import { API_ENDPOINTS } from "@/utils/constants";
import { useEffect, useState } from "react";
import {
  FiBriefcase,
  FiDollarSign,
  FiLink,
  FiMapPin,
  FiRefreshCw,
  FiSearch,
  FiSend,
} from "react-icons/fi";

export default function JobsList() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState<any>(null);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: "20",
      });

      if (search) {
        params.append("search", search);
      }

      const response = await fetch(`${API_ENDPOINTS.JOBS}?${params}`);
      const data = await response.json();

      if (data.success) {
        setJobs(data.data.jobs);
        setPagination(data.data.pagination);
      }
    } catch (error) {
      console.error("Error fetching jobs:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [page, search]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchJobs();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getMatchColor = (score: number) => {
    if (score >= 0.8)
      return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300";
    if (score >= 0.6)
      return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300";
    return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Lista de Vagas
        </h2>
        <button
          onClick={() => {
            setPage(1);
            fetchJobs();
          }}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium shadow-sm  bg-blue-600 text-white rounded-md hover:bg-blue-700 dark:bg-gray-700 dark:hover:bg-gray-800 dark:border-gray-600 dark:border  duration-300"
        >
          <FiRefreshCw className="mr-2" />
          Atualizar
        </button>
      </div>

      {/* Search */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border dark:border-gray-700">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Buscar por título, empresa ou localização..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 dark:bg-gray-700 dark:hover:bg-gray-800 dark:border-gray-600 dark:border flex items-center duration-300"
          >
            <FiSearch className="mr-2" />
            Buscar
          </button>
        </form>
      </div>

      {/* Jobs List */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border dark:border-gray-700 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-gray-500 dark:text-gray-400">
              Carregando vagas...
            </p>
          </div>
        ) : jobs.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            <FiSearch className="text-4xl mb-4 mx-auto" />
            <p>Nenhuma vaga encontrada</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {jobs.map((job: any) => (
              <div
                key={job.id}
                className="p-6 hover:bg-gray-50 dark:hover:bg-gray-750"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white truncate">
                        {job.title}
                      </h3>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getMatchColor(
                          job.match_score
                        )}`}
                      >
                        {Math.round(job.match_score * 100)}% match
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400 mb-3">
                      <span className="flex items-center">
                        <FiBriefcase className="mr-1" />
                        {job.company}
                      </span>
                      <span className="flex items-center">
                        <FiMapPin className="mr-1" />
                        {job.location}
                      </span>
                      {job.salary && (
                        <span className="flex items-center">
                          <FiDollarSign className="mr-1" />
                          {job.salary}
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-gray-400 dark:text-gray-500">
                      Encontrada em: {formatDate(job.created_at)}
                    </p>
                  </div>

                  <div className="ml-4 flex-shrink-0 flex flex-col gap-2">
                    {job.url && (
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800"
                      >
                        <FiLink className="mr-1" />
                        Ver Vaga
                      </a>
                    )}
                    <button className="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-650">
                      <FiSend className="mr-1" />
                      Candidatar
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination && pagination.pages > 1 && (
        <div className="flex items-center justify-between bg-white dark:bg-gray-800 px-4 py-3 border dark:border-gray-700 rounded-lg">
          <div className="flex justify-between items-center w-full">
            <div>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                Mostrando {(pagination.page - 1) * pagination.per_page + 1} até{" "}
                {Math.min(
                  pagination.page * pagination.per_page,
                  pagination.total
                )}{" "}
                de {pagination.total} vagas
              </p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page <= 1}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-650 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Anterior
              </button>
              <span className="px-3 py-1 text-sm text-gray-700 dark:text-gray-300">
                {page} de {pagination.pages}
              </span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= pagination.pages}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-650 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Próxima
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
