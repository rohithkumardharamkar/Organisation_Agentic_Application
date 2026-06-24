import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/v1";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to inject JWT Token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("finpilot_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export const api = {
  // Auth
  auth: {
    signup: async (data: any) => {
      const resp = await apiClient.post("/auth/signup", data);
      return resp.data;
    },
    login: async (formData: URLSearchParams) => {
      const resp = await apiClient.post("/auth/login", formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });
      return resp.data;
    },
    googleLogin: async (payload: any) => {
      const resp = await apiClient.post("/auth/google-login", payload);
      return resp.data;
    },
    otpLogin: async (data: { email: string; otp: string }) => {
      const resp = await apiClient.post("/auth/otp-login", data);
      return resp.data;
    },
    forgotPassword: async (email: string) => {
      const resp = await apiClient.post("/auth/forgot-password", { email });
      return resp.data;
    },
  },
  

  // Copilot
  copilot: {
    history: async () => {
      const resp = await apiClient.get("/copilot/history");
      return resp.data;
    },
    status: async () => {
      const resp = await apiClient.get("/copilot/status");
      return resp.data;
    },
    chat: async (message: string) => {
      const resp = await apiClient.post("/copilot/chat", { message });
      return resp.data;
    },
    approve: async (approve: boolean) => {
      const resp = await apiClient.post("/copilot/approve", { approve });
      return resp.data;
    },
  },
  
  // Dashboards
  dashboards: {
    executive: async () => {
      const resp = await apiClient.get("/dashboards/executive");
      return resp.data;
    },
    workforce: async () => {
      const resp = await apiClient.get("/dashboards/workforce");
      return resp.data;
    },
    projects: async () => {
      const resp = await apiClient.get("/dashboards/projects");
      return resp.data;
    },
    talent: async () => {
      const resp = await apiClient.get("/dashboards/talent");
      return resp.data;
    },
    getByRole: async (role: string) => {
      const resp = await apiClient.get(`/dashboards/role/${encodeURIComponent(role)}`);
      return resp.data;
    },
  },
  
  // Knowledge
  knowledge: {
    list: async () => {
      const resp = await apiClient.get("/knowledge/documents");
      return resp.data;
    },
    upload: async (file: File, category: string, allowedRoles: string) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("category", category);
      formData.append("allowed_roles", allowedRoles);
      
      const resp = await apiClient.post("/knowledge/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return resp.data;
    },
    delete: async (docId: number) => {
      const resp = await apiClient.delete(`/knowledge/documents/${docId}`);
      return resp.data;
    },
  },
  
  // AI Operations
  aiOps: {
    activities: async () => {
      const resp = await apiClient.get("/ai-ops/activities");
      return resp.data;
    },
    approvals: async () => {
      const resp = await apiClient.get("/ai-ops/approvals");
      return resp.data;
    },
    approve: async (approvalId: string) => {
      const resp = await apiClient.post(`/ai-ops/approvals/${approvalId}/approve`);
      return resp.data;
    },
    reject: async (approvalId: string) => {
      const resp = await apiClient.post(`/ai-ops/approvals/${approvalId}/reject`);
      return resp.data;
    },
    registry: async () => {
      const resp = await apiClient.get("/ai-ops/registry");
      return resp.data;
    },
    metrics: async () => {
      const resp = await apiClient.get("/ai-ops/metrics");
      return resp.data;
    },
  },

  // Evaluations
  evaluations: {
    runs: async () => {
      const resp = await apiClient.get("/evaluations/runs");
      return resp.data;
    },
    results: async (runId: number) => {
      const resp = await apiClient.get(`/evaluations/runs/${runId}/results`);
      return resp.data;
    },
    run: async () => {
      const resp = await apiClient.post("/evaluations/run");
      return resp.data;
    },
  },
};
export default apiClient;


