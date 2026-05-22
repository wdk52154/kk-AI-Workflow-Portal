// 康康 AI 全系统共享 TypeScript 类型定义

// ==================== 通用 API 响应 ====================
export interface ApiResponse<T = unknown> {
  code: number;
  data: T;
  message: string;
  trace_id: string;
}

// ==================== 项目 / 租户 ====================
export interface Project {
  id: string;
  name: string;
  api_key: string;
  quota: {
    daily: number;
    monthly: number;
  };
  created_at: string;
}

// ==================== MCP HUB 相关 ====================
export interface McpRequest {
  project_id: string;
  endpoint: string;
  payload: unknown;
  trace_id: string;
}

export interface McpRoute {
  path: string;
  service: string;
  port: number;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
}

// ==================== LLM 网关 ====================
export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
}

export interface EmbeddingRequest {
  model: string;
  input: string | string[];
}

// ==================== RAG 服务 ====================
export interface IngestDocumentRequest {
  project_id: string;
  document: {
    title: string;
    content: string;
    source_type: 'txt' | 'pdf' | 'md' | 'html';
    tags?: string[];
  };
}

export interface SearchKnowledgeRequest {
  project_id: string;
  query: string;
  top_k?: number;
  filters?: {
    source_type?: string;
    date_range?: [string, string];
    tags?: string[];
  };
}

export interface KnowledgeResult {
  id: string;
  content: string;
  score: number;
  metadata: Record<string, unknown>;
}

// ==================== 记忆服务 ====================
export interface MemoryEntry {
  session_id: string;
  user_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface UserFact {
  user_id: string;
  fact: string;
  category: string;
  confidence: number;
  source_project: string;
  created_at: string;
}

// ==================== Prompt 中心 ====================
export interface PromptTemplate {
  id: string;
  name: string;
  category: 'system' | 'user' | 'assistant' | 'tool' | 'rag' | 'sales' | 'voice';
  template: string;
  variables: string[];
  version: number;
  updated_at: string;
}

export interface RenderPromptRequest {
  variables: Record<string, string>;
}

// ==================== 素材平台 ====================
export interface Asset {
  id: string;
  name: string;
  type: 'image' | 'video' | 'poster';
  url: string;
  thumbnail_url?: string;
  tags: string[];
  size: number;
  mime_type: string;
  created_at: string;
}

// ==================== 主题 ====================
export type Theme = 'light' | 'dark' | 'system';
