import { type ClassValue, clsx } from 'clsx';

/**
 * 合并 className 工具函数
 * 使用 clsx 处理条件类名（替代 tailwind-merge + clsx 组合）
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}
