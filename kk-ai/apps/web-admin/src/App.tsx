import { useState } from "react";
import { Routes, Route, useNavigate, useLocation } from "react-router-dom";
import {
  DashboardOutlined,
  ExperimentOutlined,
  DatabaseOutlined,
  SafetyOutlined,
  AlertOutlined,
  SettingOutlined,
  SunOutlined,
  MoonOutlined,
  ThunderboltOutlined,
  ApiOutlined,
  GlobalOutlined,
  CheckCircleOutlined,
  SaveOutlined,
  DesktopOutlined,
  CodeOutlined,
  CloudServerOutlined,
} from "@ant-design/icons";
import { ProLayout, ProCard, StatisticCard } from "@ant-design/pro-components";
import { Button, Space, Tag, Tooltip, Badge, Divider, message } from "antd";
import type { Theme } from "@kk-ai/types";
import { generateTraceId, storage } from "@kk-ai/utils";
import type { Project } from "@kk-ai/types";
import QuotaPage from "./pages/quota";

/* ─── props from ThemeWrapper ─── */
interface AppProps {
  theme: Theme;
  resolvedTheme: "light" | "dark";
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
}

function DashboardPage({
  theme,
  resolvedTheme,
  setTheme,
  toggleTheme,
}: AppProps) {
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
    message.success("项目信息已保存到 localStorage");
  };

  return (
    <>
      <Space direction="vertical" size={0} style={{ marginBottom: 24 }}>
        <span style={{ fontSize: 20, fontWeight: 700 }}>中台管理后台</span>
        <Space size={12} style={{ marginTop: 4 }}>
          <span style={{ color: "#8c8c8c", fontSize: 13 }}>
            Monorepo 全栈 AI 系统 · 实时监控与配置中心
          </span>
          <Tag color="blue" style={{ fontSize: 11, margin: 0 }}>
            Trace: {traceId.slice(0, 8)}
          </Tag>
        </Space>
      </Space>

      {/* ─── 统计卡片 ─── */}
      <StatisticCard.Group
        direction="row"
        gutter={[16, 16]}
        style={{ marginBottom: 24 }}
      >
        <StatisticCard
          statistic={{
            title: "今日调用",
            value: "8,432",
            description: (
              <span style={{ color: "#52c41a" }}>↑ 12.5% 较昨日</span>
            ),
            icon: <ApiOutlined style={{ color: "#2563eb", fontSize: 24 }} />,
          }}
          style={{ flex: 1 }}
        />
        <StatisticCard
          statistic={{
            title: "活跃项目",
            value: "24",
            description: <span style={{ color: "#52c41a" }}>+3 本月新增</span>,
            icon: <GlobalOutlined style={{ color: "#10b981", fontSize: 24 }} />,
          }}
          style={{ flex: 1 }}
        />
        <StatisticCard
          statistic={{
            title: "平均延迟",
            value: "142ms",
            description: <span style={{ color: "#8c8c8c" }}>稳定</span>,
            icon: (
              <ThunderboltOutlined style={{ color: "#f59e0b", fontSize: 24 }} />
            ),
          }}
          style={{ flex: 1 }}
        />
        <StatisticCard
          statistic={{
            title: "异常告警",
            value: "0",
            description: <span style={{ color: "#52c41a" }}>全部正常</span>,
            icon: (
              <ThunderboltOutlined style={{ color: "#ef4444", fontSize: 24 }} />
            ),
          }}
          style={{ flex: 1 }}
        />
      </StatisticCard.Group>

      {/* ─── 内容卡片 ─── */}
      <ProCard gutter={[16, 16]} wrap style={{ marginBottom: 24 }}>
        {/* 主题切换 */}
        <ProCard
          title="主题切换"
          subTitle="light / dark / system 三模式"
          bordered
          headerBordered
          extra={
            <Tag color={resolvedTheme === "dark" ? "purple" : "blue"}>
              {resolvedTheme}
            </Tag>
          }
          style={{ flex: 1, minWidth: 320 }}
        >
          <Space wrap>
            <Button icon={<SunOutlined />} onClick={() => setTheme("light")}>
              亮色
            </Button>
            <Button icon={<MoonOutlined />} onClick={() => setTheme("dark")}>
              暗色
            </Button>
            <Button
              icon={<DesktopOutlined />}
              onClick={() => setTheme("system")}
            >
              系统
            </Button>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={toggleTheme}
            >
              切换
            </Button>
          </Space>
        </ProCard>

        {/* UI 组件 */}
        <ProCard
          title="UI 组件"
          subTitle="@kk-ai/ui 共享组件库"
          bordered
          headerBordered
          extra={<Tag color="success">Ant Design</Tag>}
          style={{ flex: 1, minWidth: 320 }}
        >
          <Space wrap>
            <Button type="primary">主要</Button>
            <Button>默认</Button>
            <Button type="dashed">虚线</Button>
            <Button type="text">文字</Button>
            <Button type="primary" danger>
              危险
            </Button>
            <Button type="primary" loading>
              加载
            </Button>
          </Space>
        </ProCard>

        {/* 工具库 */}
        <ProCard
          title="类型 & 工具"
          subTitle="Workspace 联动测试"
          bordered
          headerBordered
          extra={<Tag color="processing">Workspace</Tag>}
          style={{ flex: 1, minWidth: 320 }}
        >
          <Space direction="vertical" size={8} style={{ width: "100%" }}>
            {[
              { label: "项目名称", value: demoProject.name },
              {
                label: "日配额",
                value: demoProject.quota.daily.toLocaleString(),
              },
              {
                label: "月配额",
                value: demoProject.quota.monthly.toLocaleString(),
              },
            ].map((item) => (
              <div
                key={item.label}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "8px 12px",
                  background:
                    "var(--ant-color-bg-container-secondary, #f5f5f5)",
                  borderRadius: 6,
                  fontSize: 13,
                }}
              >
                <span style={{ color: "#8c8c8c" }}>{item.label}</span>
                <span style={{ fontWeight: 600 }}>{item.value}</span>
              </div>
            ))}
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSaveProject}
              style={{ marginTop: 8 }}
            >
              保存到 Storage
            </Button>
          </Space>
        </ProCard>

        {/* 技术栈 */}
        <ProCard
          title="技术栈"
          subTitle="Monorepo 架构确认"
          bordered
          headerBordered
          extra={<Tag color="warning">v0.1.0</Tag>}
          style={{ flex: 1, minWidth: 320 }}
        >
          <Space direction="vertical" size={8} style={{ width: "100%" }}>
            {[
              "pnpm workspace + Turbo 构建编排",
              "Vite + React 18 + TypeScript Strict",
              "Ant Design + ProComponents 主题系统",
              "FastAPI Gateway (mcp-hub:8000)",
              "@kk-ai/ui / utils / types 共享包",
            ].map((text) => (
              <div
                key={text}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "8px 12px",
                  borderRadius: 6,
                  fontSize: 13,
                  color: "#595959",
                  background:
                    "var(--ant-color-bg-container-secondary, #f5f5f5)",
                }}
              >
                <span style={{ color: "#52c41a", fontSize: 14 }}>
                  <CheckCircleOutlined />
                </span>
                <span>{text}</span>
              </div>
            ))}
          </Space>
        </ProCard>
      </ProCard>

      <Divider style={{ margin: "12px 0" }} />
      <div style={{ textAlign: "center", color: "#bfbfbf", fontSize: 12 }}>
        康康 AI 全栈系统 · Monorepo 架构 · {new Date().getFullYear()}
      </div>
    </>
  );
}

export default function App({
  theme,
  resolvedTheme,
  setTheme,
  toggleTheme,
}: AppProps) {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const themeIcon =
    resolvedTheme === "dark" ? <SunOutlined /> : <MoonOutlined />;

  const routeConfig = {
    path: "/",
    routes: [
      { path: "/", name: "总览", icon: <DashboardOutlined /> },
      { path: "/quota", name: "配额管理", icon: <DatabaseOutlined /> },
      { path: "/models", name: "模型管理", icon: <ExperimentOutlined /> },
      { path: "/data", name: "数据看板", icon: <DatabaseOutlined /> },
      { path: "/auth", name: "权限管理", icon: <SafetyOutlined /> },
      { path: "/monitor", name: "监控告警", icon: <AlertOutlined /> },
      { path: "/settings", name: "项目设置", icon: <SettingOutlined /> },
    ],
  };

  return (
    <ProLayout
      title="康康 AI"
      logo={
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: "linear-gradient(135deg, #2563eb, #7c3aed)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#fff",
            fontSize: 18,
          }}
        >
          <ThunderboltOutlined />
        </div>
      }
      layout="mix"
      fixSiderbar
      fixedHeader
      collapsed={collapsed}
      onCollapse={setCollapsed}
      route={routeConfig}
      location={location}
      menuItemRender={(item, dom) => (
        <div onClick={() => item.path && navigate(item.path)}>{dom}</div>
      )}
      actionsRender={() => [
        <Tooltip title={`当前: ${theme}，点击切换`} key="theme">
          <Button
            type="text"
            icon={themeIcon}
            onClick={toggleTheme}
            style={{ fontSize: 16 }}
          />
        </Tooltip>,
        <Badge dot key="notice">
          <Button type="text" icon={<AlertOutlined />} />
        </Badge>,
      ]}
      avatarProps={{
        src: "https://gw.alipayobjects.com/zos/antfincdn/efFD%24IOql2/weixintupian_20170331104822.jpg",
        size: "small",
        title: "管理员",
      }}
      pageTitleRender={() => "中台管理后台"}
      contentStyle={{ padding: 24, minHeight: "calc(100vh - 56px)" }}
    >
      <Routes>
        <Route
          path="/"
          element={
            <DashboardPage
              theme={theme}
              resolvedTheme={resolvedTheme}
              setTheme={setTheme}
              toggleTheme={toggleTheme}
            />
          }
        />
        <Route path="/quota" element={<QuotaPage />} />
      </Routes>
    </ProLayout>
  );
}
