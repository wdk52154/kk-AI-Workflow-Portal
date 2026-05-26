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

export interface PendingAnnotationItem {
  id: number;
  raw_data_id: number;
  cleaned_content: string;
  quality_score: number | null;
  created_at: string;
}

export interface PendingAnnotationResponse {
  items: PendingAnnotationItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AnnotationRequest {
  intent?: string;
  emotion?: string;
  quality_score?: number;
  tags?: string[];
  notes?: string;
}

export interface AnnotationResponse {
  record_id: number;
  annotation_id: number;
  status: string;
  message: string;
}

export interface AnnotationStatsResponse {
  total_records: number;
  annotated_count: number;
  pending_count: number;
  annotation_rate: number;
  intent_distribution: Record<string, number>;
  emotion_distribution: Record<string, number>;
  tag_distribution: Record<string, number>;
}

export const annotationApi = {
  getPending(params?: {
    project_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<PendingAnnotationResponse> {
    const searchParams = new URLSearchParams();
    if (params?.project_id) searchParams.set("project_id", params.project_id);
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.page_size)
      searchParams.set("page_size", String(params.page_size));
    const query = searchParams.toString();
    return request<PendingAnnotationResponse>(
      `/v1/data/pending_annotation${query ? `?${query}` : ""}`,
    );
  },

  annotate(
    recordId: number,
    data: AnnotationRequest,
  ): Promise<AnnotationResponse> {
    return request<AnnotationResponse>(`/v1/data/${recordId}/annotate`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  getStats(projectId?: string): Promise<AnnotationStatsResponse> {
    const searchParams = new URLSearchParams();
    if (projectId) searchParams.set("project_id", projectId);
    const query = searchParams.toString();
    return request<AnnotationStatsResponse>(
      `/v1/data/annotation_stats${query ? `?${query}` : ""}`,
    );
  },
};
