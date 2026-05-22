// 康康 AI 共享工具库

import type { ApiResponse } from '@kk-ai/types';

/**
 * 生成唯一 trace_id
 */
export function generateTraceId(): string {
  return `trace_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * 统一 API 响应包装
 */
export function createResponse<T>(data: T, message = 'ok', code = 0): ApiResponse<T> {
  return {
    code,
    data,
    message,
    trace_id: generateTraceId(),
  };
}

/**
 * 格式化日期
 */
export function formatDate(date: Date | string | number, fmt = 'yyyy-MM-dd HH:mm:ss'): string {
  const d = new Date(date);
  const o: Record<string, number> = {
    'M+': d.getMonth() + 1,
    'd+': d.getDate(),
    'H+': d.getHours(),
    'm+': d.getMinutes(),
    's+': d.getSeconds(),
  };
  let result = fmt;
  if (/(y+)/.test(result)) {
    result = result.replace(RegExp.$1, `${d.getFullYear()}`.substring(4 - RegExp.$1.length));
  }
  for (const k in o) {
    if (new RegExp(`(${k})`).test(result)) {
      const pad = RegExp.$1.length === 1 ? '' : '00';
      result = result.replace(RegExp.$1, `${pad}${o[k]}`.substring(`${o[k]}`.length));
    }
  }
  return result;
}

/**
 * 防抖
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay = 300
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout> | null = null;
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/**
 * 节流
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
  fn: T,
  limit = 300
): (...args: Parameters<T>) => void {
  let inThrottle = false;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      fn(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * 本地存储封装（带 JSON 解析）
 */
export const storage = {
  get<T>(key: string, defaultValue?: T): T | undefined {
    try {
      const item = localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : defaultValue;
    } catch {
      return defaultValue;
    }
  },
  set(key: string, value: unknown): void {
    localStorage.setItem(key, JSON.stringify(value));
  },
  remove(key: string): void {
    localStorage.removeItem(key);
  },
};
