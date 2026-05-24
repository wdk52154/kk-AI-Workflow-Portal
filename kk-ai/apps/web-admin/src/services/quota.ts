const API_BASE =
  (import.meta as unknown as { env: Record<string, string> }).env
    .VITE_API_BASE_URL || "http://localhost:8000";

interface ApiError {
  error: string;
  message: string;
  detail?: Record<string, unknown>;
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      error: "UNKNOWN_ERROR",
      message: `HTTP ${response.status}`,
    }));
    throw new Error(error.message || error.error);
  }

  return response.json() as Promise<T>;
}

export interface QuotaRule {
  id: string;
  project_name: string;
  daily_limit: number;
  monthly_limit: number;
  alert_threshold: number;
  status: "active" | "deleted";
  created_at: string;
  updated_at: string;
}

export interface QuotaRuleListResponse {
  items: QuotaRule[];
  total: number;
  page: number;
  page_size: number;
}

export interface QuotaRuleCreate {
  project_name: string;
  daily_limit: number;
  monthly_limit: number;
  alert_threshold: number;
}

export interface QuotaRuleUpdate {
  daily_limit?: number;
  monthly_limit?: number;
  alert_threshold?: number;
  status?: "active" | "deleted";
}

export interface QuotaUsage {
  project_name: string;
  daily_used: number;
  daily_limit: number;
  monthly_used: number;
  monthly_limit: number;
  usage_rate: number;
  status: "normal" | "warning" | "exceeded";
}

export interface ProjectListResponse {
  items: string[];
}

export interface QuotaQueryParams {
  project_name?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export const quotaApi = {
  getRules(params?: QuotaQueryParams): Promise<QuotaRuleListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.project_name)
      searchParams.set("project_name", params.project_name);
    if (params?.status) searchParams.set("status", params.status);
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.page_size)
      searchParams.set("page_size", String(params.page_size));
    const query = searchParams.toString();
    return request<QuotaRuleListResponse>(
      `/api/v1/quota/rules${query ? `?${query}` : ""}`,
    );
  },

  createRule(data: QuotaRuleCreate): Promise<QuotaRule> {
    return request<QuotaRule>("/api/v1/quota/rules", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  updateRule(id: string, data: QuotaRuleUpdate): Promise<QuotaRule> {
    return request<QuotaRule>(`/api/v1/quota/rules/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  deleteRule(id: string): Promise<void> {
    return request<void>(`/api/v1/quota/rules/${id}`, {
      method: "DELETE",
    });
  },

  getUsage(): Promise<QuotaUsage[]> {
    return request<QuotaUsage[]>("/api/v1/quota/usage");
  },

  getProjectUsage(project_name: string): Promise<QuotaUsage> {
    return request<QuotaUsage>(
      `/api/v1/quota/usage/${encodeURIComponent(project_name)}`,
    );
  },

  getProjects(): Promise<ProjectListResponse> {
    return request<ProjectListResponse>("/api/v1/quota/projects");
  },
};
