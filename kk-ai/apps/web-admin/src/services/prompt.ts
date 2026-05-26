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

export interface PromptListItem {
  prompt_id: string;
  name: string;
  category: string;
  version: string;
  description?: string;
}

export interface PromptListResponse {
  items: PromptListItem[];
  total: number;
}

export interface PromptDetail {
  id: string;
  name: string;
  category: string;
  version: string;
  description?: string;
  template: string;
  variables?: Array<{
    name: string;
    default?: string;
    description?: string;
  }>;
}

export interface RegisterPromptRequest {
  id: string;
  name: string;
  category: string;
  template: string;
  variables?: Array<{
    name: string;
    default?: string;
    description?: string;
  }>;
  description?: string;
}

export interface RegisterPromptResponse {
  prompt_id: string;
  version: string;
}

export interface RenderPromptRequest {
  variables: Record<string, string>;
}

export interface RenderPromptResponse {
  prompt_id: string;
  rendered: string;
  variables_used: string[];
  variables_missing: string[];
}

export const promptApi = {
  list(category?: string): Promise<PromptListResponse> {
    const searchParams = new URLSearchParams();
    if (category) searchParams.set("category", category);
    const query = searchParams.toString();
    return request<PromptListResponse>(
      `/v1/prompts${query ? `?${query}` : ""}`,
    );
  },

  get(promptId: string): Promise<PromptDetail> {
    return request<PromptDetail>(`/v1/prompts/${encodeURIComponent(promptId)}`);
  },

  register(data: RegisterPromptRequest): Promise<RegisterPromptResponse> {
    return request<RegisterPromptResponse>("/v1/prompts", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  delete(promptId: string): Promise<void> {
    return request<void>(`/v1/prompts/${encodeURIComponent(promptId)}`, {
      method: "DELETE",
    });
  },

  render(
    promptId: string,
    variables: Record<string, string>,
  ): Promise<RenderPromptResponse> {
    return request<RenderPromptResponse>(
      `/v1/prompts/${encodeURIComponent(promptId)}/render`,
      {
        method: "POST",
        body: JSON.stringify({ variables }),
      },
    );
  },
};
