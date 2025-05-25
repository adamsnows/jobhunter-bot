/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { API_ENDPOINTS } from "@/utils/constants";
import { useEffect, useState } from "react";
import { FaLinkedin, FaSearch } from "react-icons/fa";
import { FiSettings } from "react-icons/fi";
import { ImSpinner8 } from "react-icons/im";
import { IoIosRefresh } from "react-icons/io";

export default function LinkedInScraperControl() {
  const [status, setStatus] = useState<any>(null);
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [editedConfig, setEditedConfig] = useState<any>(null);

  const fetchStatus = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.LINKEDIN.STATUS);
      const data = await response.json();
      if (data.success) {
        setStatus(data.data);
      }
    } catch (error) {
      console.error("Error fetching LinkedIn status:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchConfig = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.LINKEDIN.CONFIG);
      const data = await response.json();
      if (data.success) {
        setConfig(data.data);
        setEditedConfig(data.data);
      }
    } catch (error) {
      console.error("Error fetching LinkedIn config:", error);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchConfig();
    const interval = setInterval(fetchStatus, 5000); // Check status every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const handleStartScraper = async () => {
    setActionLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.LINKEDIN.START, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(config),
      });
      const data = await response.json();
      if (data.success) {
        alert("✅ LinkedIn Scraper iniciado com sucesso!");
        fetchStatus();
      } else {
        alert(
          `❌ Erro ao iniciar LinkedIn Scraper: ${data.message || data.error}`
        );
      }
    } catch (error) {
      console.error("Error starting LinkedIn scraper:", error);
      alert("❌ Erro ao conectar com o servidor");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateConfig = async () => {
    setActionLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.LINKEDIN.CONFIG, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(editedConfig),
      });
      const data = await response.json();
      if (data.success) {
        alert("✅ Configuração atualizada com sucesso!");
        setConfig(editedConfig);
        setShowConfig(false);
      } else {
        alert(
          `❌ Erro ao atualizar configuração: ${data.message || data.error}`
        );
      }
    } catch (error) {
      console.error("Error updating LinkedIn config:", error);
      alert("❌ Erro ao conectar com o servidor");
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (isoString: string) => {
    if (!isoString) return "";
    return new Date(isoString).toLocaleString();
  };

  const handleInputChange = (section: string, key: string, value: any) => {
    setEditedConfig((prev: any) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
  };

  const handleKeywordsChange = (value: string) => {
    const keywords = value
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean);
    setEditedConfig((prev: any) => ({
      ...prev,
      search_config: {
        ...prev.search_config,
        keywords,
      },
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <ImSpinner8 className="animate-spin text-2xl text-blue-500 mr-2" />
        <span>Carregando...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold flex items-center">
          <FaLinkedin className="text-[#0A66C2] mr-2" />
          LinkedIn Scraper
        </h2>
        <div className="flex space-x-2">
          <button
            onClick={fetchStatus}
            className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full"
            title="Atualizar status"
          >
            <IoIosRefresh />
          </button>
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full"
            title="Configurações"
          >
            <FiSettings />
          </button>
        </div>
      </div>

      {/* Status Card */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <div
            className={`w-3 h-3 rounded-full mr-2 ${
              status?.running
                ? "bg-green-500 animate-pulse"
                : status?.results?.status === "error"
                ? "bg-red-500"
                : "bg-gray-500"
            }`}
          ></div>
          <span className="font-medium">
            {status?.running
              ? "Em execução"
              : status?.results?.status === "error"
              ? "Erro"
              : status?.results?.status === "completed"
              ? "Concluído"
              : "Inativo"}
          </span>
        </div>

        {status?.results && (
          <div className="space-y-2 text-sm">
            {status.results.start_time && (
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">
                  Início:
                </span>
                <span>{formatDate(status.results.start_time)}</span>
              </div>
            )}
            {status.results.end_time && (
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">
                  Término:
                </span>
                <span>{formatDate(status.results.end_time)}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">
                Vagas encontradas:
              </span>
              <span>{status.results.jobs_found}</span>
            </div>
            {status.results.error && (
              <div className="mt-2 text-red-500 text-xs">
                <p className="font-medium">Erro:</p>
                <p className="break-all">{status.results.error}</p>
              </div>
            )}
          </div>
        )}

        <div className="mt-6">
          <button
            onClick={handleStartScraper}
            disabled={status?.running || actionLoading}
            className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLoading ? (
              <ImSpinner8 className="animate-spin mr-2" />
            ) : (
              <FaSearch className="mr-2" />
            )}
            {actionLoading
              ? "Processando..."
              : status?.running
              ? "Scraper em execução"
              : "Iniciar busca no LinkedIn"}
          </button>
        </div>
      </div>

      {/* Configuration */}
      {showConfig && config && (
        <div className="bg-white dark:bg-gray-800 shadow-sm border dark:border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-medium mb-4">
            Configurações do LinkedIn Scraper
          </h3>

          <div className="space-y-4">
            {/* LinkedIn Credentials */}
            <div>
              <h4 className="font-medium text-sm text-gray-700 dark:text-gray-300 mb-2">
                Credenciais
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">
                    Email/Username
                  </label>
                  <input
                    type="text"
                    value={editedConfig?.linkedin?.username || ""}
                    onChange={(e) =>
                      handleInputChange("linkedin", "username", e.target.value)
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">
                    Senha
                  </label>
                  <input
                    type="password"
                    placeholder="********"
                    onChange={(e) =>
                      handleInputChange("linkedin", "password", e.target.value)
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>
            </div>

            {/* Search Parameters */}
            <div>
              <h4 className="font-medium text-sm text-gray-700 dark:text-gray-300 mb-2">
                Parâmetros de Busca
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="sm:col-span-2">
                  <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">
                    Palavras-chave (separadas por vírgula)
                  </label>
                  <textarea
                    value={
                      editedConfig?.search_config?.keywords?.join(", ") || ""
                    }
                    onChange={(e) => handleKeywordsChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    rows={2}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">
                    Localização
                  </label>
                  <input
                    type="text"
                    value={editedConfig?.search?.location || ""}
                    onChange={(e) =>
                      handleInputChange("search", "location", e.target.value)
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">
                    Mínimo de matches
                  </label>
                  <input
                    type="number"
                    value={editedConfig?.filters?.min_keyword_matches || 2}
                    onChange={(e) =>
                      handleInputChange(
                        "filters",
                        "min_keyword_matches",
                        parseInt(e.target.value)
                      )
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex justify-end space-x-3 pt-4">
              <button
                onClick={() => setShowConfig(false)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-650"
              >
                Cancelar
              </button>
              <button
                onClick={handleUpdateConfig}
                disabled={actionLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading ? (
                  <>
                    <ImSpinner8 className="animate-spin inline mr-2" />
                    Salvando...
                  </>
                ) : (
                  "Salvar Configurações"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
