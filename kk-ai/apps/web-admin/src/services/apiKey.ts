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
      "X-Admin-Key": "admin-secret-key",
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

export interface ApiKeyItem {
  id: string;
  project_name: string;
  key_prefix: string;
  status: "active" | "disabled" | "deleted";
  daily_limit: number;
  monthly_limit: number;
  alert_threshold: number;
  created_at: string;
  updated_at: string;
}

export interface ApiKeyListResponse {
  items: ApiKeyItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiKeyCreateRequest {
  project_name: string;
  daily_limit: number;
  monthly_limit: number;
  alert_threshold: number;
}

export interface ApiKeyCreateResponse {
  id: string;
  api_key: string;
  project_name: string;
}

export interface ApiKeyUpdateRequest {
  daily_limit?: number;
  monthly_limit?: number;
  alert_threshold?: number;
  status?: "active" | "disabled" | "deleted";
}

export const apiKeyApi = {
  getList(params?: {
    page?: number;
    page_size?: number;
    project_name?: string;
  }): Promise<ApiKeyListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.page_size)
      searchParams.set("page_size", String(params.page_size));
    if (params?.project_name)
      searchParams.set("project_name", params.project_name);
    const query = searchParams.toString();
    return request<ApiKeyListResponse>(
      `/api/v1/admin/api-keys${query ? `?${query}` : ""}`,
    );
  },

  create(data: ApiKeyCreateRequest): Promise<ApiKeyCreateResponse> {
    return request<ApiKeyCreateResponse>("/api/v1/admin/api-keys", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  update(id: string, data: ApiKeyUpdateRequest): Promise<ApiKeyItem> {
    return request<ApiKeyItem>(
      `/api/v1/admin/api-keys/${encodeURIComponent(id)}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      },
    );
  },

  delete(id: string): Promise<void> {
    return request<void>(`/api/v1/admin/api-keys/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
  },
};
