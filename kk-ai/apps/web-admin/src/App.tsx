import { useState } from 'react';
import { Button, useTheme } from '@kk-ai/ui';
import { generateTraceId, storage } from '@kk-ai/utils';
import type { Project } from '@kk-ai/types';

function App() {
  const { theme, setTheme, toggleTheme, resolvedTheme } = useTheme();
  const [traceId] = useState(() => generateTraceId());

  const demoProject: Project = {
    id: 'proj_001',
    name: '康康 AI 中台',
    api_key: 'kk_live_xxxxxxxx',
    quota: { daily: 10000, monthly: 300000 },
    created_at: new Date().toISOString(),
  };

  const handleSaveProject = () => {
    storage.set('demo_project', demoProject);
    alert('项目信息已保存到 localStorage');
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-2">康康 AI · 中台管理后台</h1>
        <p className="text-muted-foreground">
          Monorepo 初始化验证页面 | Trace ID: {traceId}
        </p>
      </header>

      <section className="grid gap-6 max-w-2xl">
        {/* 主题切换 */}
        <div className="rounded-lg border p-6">
          <h2 className="text-xl font-semibold mb-4">主题切换测试</h2>
          <div className="flex items-center gap-4 mb-4">
            <span className="text-sm text-muted-foreground">
              当前主题: <strong>{theme}</strong>（解析后: {resolvedTheme}）
            </span>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setTheme('light')}>
              亮色
            </Button>
            <Button variant="outline" size="sm" onClick={() => setTheme('dark')}>
              暗色
            </Button>
            <Button variant="outline" size="sm" onClick={() => setTheme('system')}>
              跟随系统
            </Button>
            <Button variant="secondary" size="sm" onClick={toggleTheme}>
              切换
            </Button>
          </div>
        </div>

        {/* 组件库测试 */}
        <div className="rounded-lg border p-6">
          <h2 className="text-xl font-semibold mb-4">UI 组件测试</h2>
          <div className="flex flex-wrap gap-2">
            <Button>默认按钮</Button>
            <Button variant="secondary">次要按钮</Button>
            <Button variant="outline">边框按钮</Button>
            <Button variant="ghost">幽灵按钮</Button>
            <Button variant="danger">危险按钮</Button>
            <Button loading>加载中</Button>
          </div>
        </div>

        {/* 工具库测试 */}
        <div className="rounded-lg border p-6">
          <h2 className="text-xl font-semibold mb-4">工具库 & 类型测试</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Project 名称: {demoProject.name} | 日配额: {demoProject.quota.daily}
          </p>
          <Button onClick={handleSaveProject}>保存项目到 Storage</Button>
        </div>

        {/* 技术栈确认 */}
        <div className="rounded-lg border p-6">
          <h2 className="text-xl font-semibold mb-4">技术栈确认</h2>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>✅ pnpm workspace + strict-peer-dependencies=false</li>
            <li>✅ Vite + React 18 + TypeScript</li>
            <li>✅ Tailwind CSS + shadcn/ui 设计规范</li>
            <li>✅ 主题切换（light / dark / system）</li>
            <li>✅ @kk-ai/ui / utils / types workspace 联动</li>
          </ul>
        </div>
      </section>
    </div>
  );
}

export default App;
