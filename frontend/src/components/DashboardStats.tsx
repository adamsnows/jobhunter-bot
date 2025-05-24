"use client";
import { CiSearch, CiSettings, CiStreamOff, CiStreamOn } from "react-icons/ci";
import { FaChartBar, FaSearch } from "react-icons/fa";
import { GiSchoolBag } from "react-icons/gi";
import {
  MdOutlineMarkEmailRead,
  MdOutlineShowChart,
  MdQueryStats,
} from "react-icons/md";
import { SiMinutemailer } from "react-icons/si";

interface DashboardStatsProps {
  stats: any;
}

export default function DashboardStats({ stats }: DashboardStatsProps) {
  if (!stats) {
    return (
      <div className="animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="bg-white dark:bg-gray-800 shadow-sm border dark:border-gray-700 rounded-lg overflow-hidden"
            >
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const statCards = [
    {
      title: "Total de Vagas",
      value: stats.total_jobs || 0,
      icon: <GiSchoolBag />,
      change: `+${stats.jobs_today || 0} hoje`,
      changeType: "positive" as const,
    },
    {
      title: "Candidaturas Enviadas",
      value: stats.total_applications || 0,
      icon: <MdOutlineMarkEmailRead />,
      change: `+${stats.applications_today || 0} hoje`,
      changeType: "positive" as const,
    },
    {
      title: "Taxa de Sucesso",
      value: `${stats.success_rate || 0}%`,
      icon: <MdOutlineShowChart />,
      change: "dos envios",
      changeType: "neutral" as const,
    },
    {
      title: "Status do Bot",
      value: stats.daemon_running ? "Ativo" : "Parado",
      icon: stats.daemon_running ? <CiStreamOn /> : <CiStreamOff />,
      change: stats.daemon_running ? "Procurando vagas" : "Inativo",
      changeType: stats.daemon_running ? "positive" : ("negative" as const),
    },
  ];

  return (
    <div className="space-y-8">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <div
            key={index}
            className="bg-white dark:bg-gray-800 shadow-sm border dark:border-gray-700  overflow-hidden  rounded-lg  p-6 dark:text-gray-400"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {stat.title}
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-400">
                  {stat.value}
                </p>
              </div>
              <div className="text-2xl">{stat.icon}</div>
            </div>
            <div
              className={`mt-2 flex items-center text-sm ${
                stat.changeType === "positive"
                  ? "text-green-600"
                  : stat.changeType === "negative"
                  ? "text-red-600"
                  : "text-gray-500"
              }`}
            >
              <span>{stat.change}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Jobs */}
        <div className=" dark:bg-gray-800 shadow-sm border dark:border-gray-700 rounded-lg overflow-hidden bg-white dark:text-gray-400">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-400">
              Vagas Recentes
            </h3>
          </div>
          <div className="divide-y divide-gray-200">
            {stats.recent_jobs && stats.recent_jobs.length > 0 ? (
              stats.recent_jobs.slice(0, 5).map((job: any, index: number) => (
                <div key={index} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate dark:text-gray-400">
                        {job[0]} {/* title */}
                      </p>
                      <p className="text-sm text-gray-500 truncate dark:text-gray-400">
                        {job[1]} • {job[2]} {/* company • location */}
                      </p>
                    </div>
                    <div className="ml-4 flex-shrink-0">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {Math.round((job[3] || 0) * 100)}% match
                      </span>
                    </div>
                  </div>
                  <p className="mt-1 text-xs text-gray-400">
                    {new Date(job[4]).toLocaleDateString("pt-BR")}
                  </p>
                </div>
              ))
            ) : (
              <div className="px-6 py-8 text-center text-gray-500 items-center justify-center flex flex-col">
                <span className="text-2xl mb-2 block">
                  <CiSearch />
                </span>
                Nenhuma vaga encontrada ainda
              </div>
            )}
          </div>
        </div>

        {/* Recent Applications */}
        <div className="dark:bg-gray-800 shadow-sm border dark:border-gray-700 rounded-lg overflow-hidden bg-white dark:text-gray-400">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-400">
              Candidaturas Recentes
            </h3>
          </div>
          <div className="divide-y divide-gray-200">
            {stats.recent_applications &&
            stats.recent_applications.length > 0 ? (
              stats.recent_applications
                .slice(0, 5)
                .map((app: any, index: number) => (
                  <div key={index} className="px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {app[0]} {/* job title */}
                        </p>
                        <p className="text-sm text-gray-500 truncate">
                          {app[1]} {/* company */}
                        </p>
                      </div>
                      <div className="ml-4 flex-shrink-0">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            app[2] === "sent"
                              ? "bg-green-100 text-green-800"
                              : app[2] === "failed"
                              ? "bg-red-100 text-red-800"
                              : "bg-yellow-100 text-yellow-800"
                          }`}
                        >
                          {app[2] === "sent"
                            ? "✅ Enviado"
                            : app[2] === "failed"
                            ? "❌ Falhou"
                            : "⏳ Pendente"}
                        </span>
                      </div>
                    </div>
                    <p className="mt-1 text-xs text-gray-400">
                      {new Date(app[3]).toLocaleDateString("pt-BR")}
                    </p>
                  </div>
                ))
            ) : (
              <div className="px-6 py-8 text-center text-gray-500 items-center justify-center flex flex-col">
                <span className="text-2xl mb-2 block">
                  <SiMinutemailer />
                </span>
                Nenhuma candidatura enviada ainda
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="dark:bg-gray-800  dark:border-gray-700 rounded-lg overflow-hidden  dark:text-gray-400  shadow-sm border p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4 dark:text-gray-400">
          Ações Rápidas
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <button className="dark:text-gray-400 dark:bg-gray-800 dark:border-gray-700 flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
            <span className="mr-2">
              <FaSearch />
            </span>
            Buscar Vagas Agora
          </button>
          <button className="dark:text-gray-400 dark:bg-gray-800 dark:border-gray-700 flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
            <span className="mr-2">
              <FaChartBar />
            </span>
            Relatório Detalhado
          </button>
          <button className="dark:text-gray-400 dark:bg-gray-800 dark:border-gray-700 flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
            <span className="mr-2 text-lg">
              <CiSettings />
            </span>
            Configurações
          </button>
          <button className="dark:text-gray-400 dark:bg-gray-800 dark:border-gray-700 flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
            <span className="mr-2 text-lg">
              <MdQueryStats />
            </span>
            Ver Logs
          </button>
        </div>
      </div>
    </div>
  );
}
