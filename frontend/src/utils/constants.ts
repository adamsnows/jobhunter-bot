// Define application constants

// API URLs
export const API_BASE_URL = "http://localhost:5001";
export const API_ENDPOINTS = {
  STATS: `${API_BASE_URL}/api/stats`,
  DAEMON: {
    STATUS: `${API_BASE_URL}/api/daemon/status`,
    START: `${API_BASE_URL}/api/daemon/start`,
    STOP: `${API_BASE_URL}/api/daemon/stop`,
  },
  JOBS: `${API_BASE_URL}/api/jobs`,
  APPLICATIONS: `${API_BASE_URL}/api/applications`,
  LOGS: `${API_BASE_URL}/api/logs`,
  HEALTH: `${API_BASE_URL}/api/health`,
};
