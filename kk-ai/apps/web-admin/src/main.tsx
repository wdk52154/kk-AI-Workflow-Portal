import ReactDOM from 'react-dom/client';
import { ConfigProvider, theme as antdTheme } from 'antd';
import { ProConfigProvider } from '@ant-design/pro-components';
import zhCN from 'antd/locale/zh_CN';
import { useState, useEffect } from 'react';
import { storage } from '@kk-ai/utils';
import type { Theme } from '@kk-ai/types';
import App from './App';

const THEME_STORAGE_KEY = 'kk-ai-theme';

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function resolveTheme(theme: Theme): 'light' | 'dark' {
  if (theme === 'system') return getSystemTheme();
  return theme;
}

function ThemeWrapper() {
  const [theme, setThemeState] = useState<Theme>(() => {
    return storage.get<Theme>(THEME_STORAGE_KEY, 'system') ?? 'system';
  });

  const resolvedTheme = resolveTheme(theme);
  const isDark = resolvedTheme === 'dark';

  useEffect(() => {
    const resolved = resolveTheme(theme);
    const root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(resolved);
    root.style.colorScheme = resolved;
    storage.set(THEME_STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    if (theme !== 'system') return;
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => setThemeState((prev) => prev); // trigger re-render
    media.addEventListener('change', handler);
    return () => media.removeEventListener('change', handler);
  }, [theme]);

  const setTheme = (newTheme: Theme) => setThemeState(newTheme);
  const toggleTheme = () => {
    setThemeState((prev) => {
      if (prev === 'dark') return 'light';
      if (prev === 'light') return 'dark';
      return getSystemTheme() === 'dark' ? 'light' : 'dark';
    });
  };

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: isDark ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
        token: {
          borderRadius: 8,
          colorPrimary: '#2563eb',
          colorInfo: '#2563eb',
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif",
        },
      }}
    >
      <ProConfigProvider dark={isDark}>
        <App
          theme={theme}
          resolvedTheme={resolvedTheme}
          setTheme={setTheme}
          toggleTheme={toggleTheme}
        />
      </ProConfigProvider>
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(<ThemeWrapper />);
