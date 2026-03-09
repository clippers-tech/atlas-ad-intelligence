import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// Inject account_id into every request from localStorage
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const accountId = localStorage.getItem("atlas_account_id");
    if (accountId) {
      config.params = { ...config.params, account_id: accountId };
    }
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    console.error("[ATLAS API]", error?.response?.status, error?.message);
    return Promise.reject(error);
  }
);

export default api;

// Typed helpers
export async function fetchData<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const res = await api.get<T>(url, { params });
  return res.data;
}

export async function postData<T>(url: string, data?: unknown): Promise<T> {
  const res = await api.post<T>(url, data);
  return res.data;
}

export async function patchData<T>(url: string, data?: unknown): Promise<T> {
  const res = await api.patch<T>(url, data);
  return res.data;
}

export async function deleteData<T>(url: string): Promise<T> {
  const res = await api.delete<T>(url);
  return res.data;
}
