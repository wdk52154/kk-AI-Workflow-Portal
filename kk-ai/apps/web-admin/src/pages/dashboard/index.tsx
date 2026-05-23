import { useState } from "react";
import {
  Activity,
  Box,
  Code2,
  Cpu,
  Database,
  FolderGit2,
  Gauge,
  Layers,
  Palette,
  Shield,
  Sun,
  Moon,
  Zap,
} from "lucide-react";
import { Button, useTheme } from "@kk-ai/ui";
import { generateTraceId, storage } from "@kk-ai/utils";
import type { Project } from "@kk-ai/types";
import styles from "./index.module.css";

export default function DashboardPage() {
  const { theme, setTheme, toggleTheme, resolvedTheme } = useTheme();
  const [traceId] = useState(() => generateTraceId());

  const demoProject: Project = {
    id: "proj_001",
    name: "康康 AI 中台",
    api_key: "kk_live_xxxxxxxx",
    quota: { daily: 10000, monthly: 300000 },
    created_at: new Date().toISOString(),
  };

  const handleSaveProject = () => {
    storage.set("demo_project", demoProject);
    alert("项目信息已保存到 localStorage");
  };

  return (
    <div className={styles.container}>
      {/* 欢迎区域 */}
      <div className={styles.hero}>
        <h1 className={styles.heroTitle}>中台管理后台</h1>
        <p className={styles.heroSubtitle}>
          Monorepo 全栈 AI 系统 · 实时监控与配置中心
        </p>
        <div className={styles.traceId}>
          <Activity size={12} />
          <span>Trace ID: {traceId}</span>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>今日调用</span>
            <div className={styles.statIconBlue}>
              <Gauge size={16} />
            </div>
          </div>
          <div className={styles.statValue}>8,432</div>
          <div className={styles.statChange}>+12.5% 较昨日</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>活跃项目</span>
            <div className={styles.statIconGreen}>
              <Layers size={16} />
            </div>
          </div>
          <div className={styles.statValue}>24</div>
          <div className={styles.statChange}>+3 本月新增</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>平均延迟</span>
            <div className={styles.statIconOrange}>
              <Zap size={16} />
            </div>
          </div>
          <div className={styles.statValue}>142ms</div>
          <div className={styles.statChangeNeutral}>稳定</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>异常告警</span>
            <div className={styles.statIconRed}>
              <Shield size={16} />
            </div>
          </div>
          <div className={styles.statValue}>0</div>
          <div className={styles.statChange}>全部正常</div>
        </div>
      </div>

      {/* 内容卡片 */}
      <div className={styles.contentGrid}>
        {/* 主题切换 */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.cardIconPurple}>
              <Palette size={20} />
            </div>
            <div>
              <div className={styles.cardTitle}>主题切换</div>
              <div className={styles.cardDesc}>
                light / dark / system 三模式
              </div>
            </div>
          </div>
          <div className={styles.cardBody}>
            <div className={styles.themePreview}>
              <div className={styles.themeBadge}>
                <span className={styles.themeDot} />
                {theme}
              </div>
              <span
                style={{
                  fontSize: "0.8125rem",
                  color: "var(--muted-foreground)",
                }}
              >
                解析后: {resolvedTheme}
              </span>
            </div>
            <div className={styles.buttonGroup}>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setTheme("light")}
              >
                <Sun size={14} style={{ marginRight: 4 }} />
                亮色
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setTheme("dark")}
              >
                <Moon size={14} style={{ marginRight: 4 }} />
                暗色
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setTheme("system")}
              >
                <Cpu size={14} style={{ marginRight: 4 }} />
                系统
              </Button>
              <Button variant="secondary" size="sm" onClick={toggleTheme}>
                <Zap size={14} style={{ marginRight: 4 }} />
                切换
              </Button>
            </div>
          </div>
        </div>

        {/* UI 组件测试 */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.cardIconBlue}>
              <Box size={20} />
            </div>
            <div>
              <div className={styles.cardTitle}>UI 组件</div>
              <div className={styles.cardDesc}>@kk-ai/ui 共享组件库</div>
            </div>
          </div>
          <div className={styles.cardBody}>
            <div className={styles.buttonGroup}>
              <Button>默认</Button>
              <Button variant="secondary">次要</Button>
              <Button variant="outline">边框</Button>
              <Button variant="ghost">幽灵</Button>
              <Button variant="danger">危险</Button>
              <Button loading>加载</Button>
            </div>
          </div>
        </div>

        {/* 工具库 & 类型 */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.cardIconGreen}>
              <Code2 size={20} />
            </div>
            <div>
              <div className={styles.cardTitle}>类型 & 工具</div>
              <div className={styles.cardDesc}>Workspace 联动测试</div>
            </div>
          </div>
          <div className={styles.cardBody}>
            <div className={styles.projectInfo}>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>项目名称</span>
                <span className={styles.infoValue}>{demoProject.name}</span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>日配额</span>
                <span className={styles.infoValue}>
                  {demoProject.quota.daily.toLocaleString()}
                </span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>月配额</span>
                <span className={styles.infoValue}>
                  {demoProject.quota.monthly.toLocaleString()}
                </span>
              </div>
            </div>
            <Button onClick={handleSaveProject}>
              <Database size={14} style={{ marginRight: 6 }} />
              保存到 Storage
            </Button>
          </div>
        </div>

        {/* 技术栈确认 */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.cardIconAmber}>
              <Cpu size={20} />
            </div>
            <div>
              <div className={styles.cardTitle}>技术栈</div>
              <div className={styles.cardDesc}>Monorepo 架构确认</div>
            </div>
          </div>
          <div className={styles.cardBody}>
            <ul className={styles.techList}>
              {[
                "pnpm workspace + Turbo 构建编排",
                "Vite + React 18 + TypeScript Strict",
                "CSS Modules + CSS Variables 主题系统",
                "FastAPI Gateway (mcp-hub:8000)",
                "@kk-ai/ui / utils / types 共享包",
              ].map((item) => (
                <li key={item} className={styles.techItem}>
                  <span className={styles.techCheck}>✓</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
