import { useState, useEffect } from "react";
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
  MonitorOutlined,
  EditOutlined,
  FileTextOutlined,
  KeyOutlined,
  UserOutlined,
  ClusterOutlined,
  CloudOutlined,
  CustomerServiceOutlined,
  ReadOutlined,
  VideoCameraOutlined,
  PictureOutlined,
  ShoppingCartOutlined,
  LinkOutlined,
  ArrowRightOutlined,
  PlayCircleOutlined,
  TeamOutlined,
  BugOutlined,
  SoundOutlined,
  FileImageOutlined,
  MessageOutlined,
} from "@ant-design/icons";
import { ProLayout, StatisticCard } from "@ant-design/pro-components";
import {
  Button,
  Space,
  Tag,
  Tooltip,
  Badge,
  Divider,
  Row,
  Col,
  Card,
} from "antd";
import type { Theme } from "@kk-ai/types";
import { generateTraceId } from "@kk-ai/utils";
import QuotaPage from "./pages/quota";
import QuotaRulesPage from "./pages/quota/rules";
import MonitorPage from "./pages/monitor";
import AnnotationPage from "./pages/annotation";
import PromptsPage from "./pages/prompts";
import ApiKeysPage from "./pages/apiKeys";
import UserProfilePage from "./pages/userProfile";

/* ─── props from ThemeWrapper ─── */
interface AppProps {
  theme: Theme;
  resolvedTheme: "light" | "dark";
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
}

function ServiceHealthBadge({ name, port }: { name: string; port: number }) {
  const [status, setStatus] = useState<"ok" | "down" | "checking">("checking");

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        const res = await fetch(`http://localhost:${port}/health`, {
          method: "GET",
          signal: AbortSignal.timeout(3000),
        });
        if (mounted) setStatus(res.ok ? "ok" : "down");
      } catch {
        if (mounted) setStatus("down");
      }
    };
    check();
    const id = setInterval(check, 10000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, [port]);

  const color =
    status === "ok" ? "success" : status === "down" ? "error" : "processing";
  const text =
    status === "ok" ? "运行中" : status === "down" ? "未启动" : "检测中";
  return <Badge status={color as any} text={`${name} ${text}`} />;
}

function ProjectCard({
  title,
  desc,
  icon,
  href,
  color = "#2563eb",
}: {
  title: string;
  desc: string;
  icon: React.ReactNode;
  href: string;
  color?: string;
}) {
  return (
    <Card
      hoverable
      onClick={() => window.open(href, "_blank")}
      style={{ borderRadius: 12, cursor: "pointer" }}
      bodyStyle={{ padding: 20 }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: color,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#fff",
            fontSize: 24,
          }}
        >
          {icon}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: 15 }}>{title}</div>
          <div style={{ color: "#8c8c8c", fontSize: 12, marginTop: 4 }}>
            {desc}
          </div>
        </div>
        <ArrowRightOutlined style={{ color: "#bfbfbf" }} />
      </div>
    </Card>
  );
}

function DashboardPage({ setTheme, toggleTheme }: AppProps) {
  const [traceId] = useState(() => generateTraceId());

  const backendServices = [
    { name: "MCP HUB", port: 8000 },
    { name: "LLM 网关", port: 9001 },
    { name: "RAG 服务", port: 9002 },
    { name: "记忆服务", port: 9003 },
    { name: "Prompt 中心", port: 9004 },
    { name: "数据中心", port: 9005 },
    { name: "素材平台", port: 9006 },
    { name: "销售 Agent", port: 9007 },
    { name: "语音客服", port: 9008 },
    { name: "内容运营", port: 9009 },
    { name: "直播切片", port: 9011 },
  ];

  const stage1Projects = [
    {
      title: "MCP HUB",
      desc: "MCP 中台网关 :8000",
      icon: <ApiOutlined />,
      href: "http://localhost:8000",
      color: "#2563eb",
    },
    {
      title: "LLM 网关",
      desc: "豆包 ARK 对接 :9001",
      icon: <CloudOutlined />,
      href: "http://localhost:9001",
      color: "#7c3aed",
    },
    {
      title: "RAG 服务",
      desc: "知识检索 :9002",
      icon: <ReadOutlined />,
      href: "http://localhost:9002",
      color: "#0891b2",
    },
    {
      title: "记忆服务",
      desc: "跨项目记忆 :9003",
      icon: <DatabaseOutlined />,
      href: "http://localhost:9003",
      color: "#059669",
    },
    {
      title: "Prompt 中心",
      desc: "模板引擎 :9004",
      icon: <FileTextOutlined />,
      href: "http://localhost:9004",
      color: "#d97706",
    },
    {
      title: "数据中心",
      desc: "ETL + 标注 :9005",
      icon: <ClusterOutlined />,
      href: "http://localhost:9005",
      color: "#dc2626",
    },
  ];

  const stage2Projects = [
    {
      title: "素材平台",
      desc: "多模态资产管理 :9006",
      icon: <PictureOutlined />,
      href: "http://localhost:5174",
      color: "#ec4899",
    },
    {
      title: "销售 Agent",
      desc: "话术 + 陪练 :9007",
      icon: <ShoppingCartOutlined />,
      href: "http://localhost:5175",
      color: "#f59e0b",
    },
  ];

  const stage3Projects = [
    {
      title: "语音客服",
      desc: "AI 实时语音对话 :9008",
      icon: <SoundOutlined />,
      href: "http://localhost:5176",
      color: "#10b981",
    },
    {
      title: "内容运营",
      desc: "自媒体 Agent :9009",
      icon: <EditOutlined />,
      href: "http://localhost:5177",
      color: "#8b5cf6",
    },
    {
      title: "直播切片",
      desc: "智能高光切片 :9011",
      icon: <VideoCameraOutlined />,
      href: "http://localhost:5178",
      color: "#ef4444",
    },
  ];

  const frontendProjects = [
    {
      title: "中台管理",
      desc: "管理后台 :5173",
      icon: <DashboardOutlined />,
      href: "http://localhost:5173",
      color: "#2563eb",
    },
    {
      title: "素材平台",
      desc: "素材库 + 审核 :5174",
      icon: <FileImageOutlined />,
      href: "http://localhost:5174",
      color: "#ec4899",
    },
    {
      title: "销售 Agent",
      desc: "话术助手 + 陪练 :5175",
      icon: <TeamOutlined />,
      href: "http://localhost:5175",
      color: "#f59e0b",
    },
    {
      title: "语音客服",
      desc: "C 端语音对话 :5176",
      icon: <CustomerServiceOutlined />,
      href: "http://localhost:5176",
      color: "#10b981",
    },
    {
      title: "内容运营",
      desc: "选题 + 生成 :5177",
      icon: <MessageOutlined />,
      href: "http://localhost:5177",
      color: "#8b5cf6",
    },
    {
      title: "直播切片",
      desc: "切片 + 增强 :5178",
      icon: <PlayCircleOutlined />,
      href: "http://localhost:5178",
      color: "#ef4444",
    },
  ];

  return (
    <>
      <Space direction="vertical" size={0} style={{ marginBottom: 24 }}>
        <span style={{ fontSize: 22, fontWeight: 700 }}>
          🚀 康康 AI 全栈系统中台
        </span>
        <Space size={12} style={{ marginTop: 4 }}>
          <span style={{ color: "#8c8c8c", fontSize: 13 }}>
            Monorepo 全栈 AI 系统 · 阶段一 MCP 中台 + 阶段二 B 端赋能 + 阶段三 C
            端产品
          </span>
          <Tag color="blue" style={{ fontSize: 11, margin: 0 }}>
            Trace: {traceId.slice(0, 8)}
          </Tag>
        </Space>
      </Space>

      {/* ─── 系统健康状态 ─── */}
      <Card title="🩺 服务健康状态" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          {backendServices.map((s) => (
            <Col key={s.name} span={4}>
              <ServiceHealthBadge name={s.name} port={s.port} />
            </Col>
          ))}
        </Row>
      </Card>

      {/* ─── 统计卡片 ─── */}
      <StatisticCard.Group
        direction="row"
        gutter={[16, 16]}
        style={{ marginBottom: 24 }}
      >
        <StatisticCard
          statistic={{
            title: "后端服务",
            value: "11",
            description: "全部已注册",
            icon: <ApiOutlined style={{ color: "#2563eb", fontSize: 24 }} />,
          }}
          style={{ flex: 1 }}
        />
        <StatisticCard
          statistic={{
            title: "前端项目",
            value: "6",
            description: "C 端 + B 端 + 中台",
            icon: <GlobalOutlined style={{ color: "#10b981", fontSize: 24 }} />,
          }}
          style={{ flex: 1 }}
        />
        <StatisticCard
          statistic={{
            title: "AI 能力",
            value: "7",
            description: "Pipeline 阶段覆盖",
            icon: (
              <ThunderboltOutlined style={{ color: "#f59e0b", fontSize: 24 }} />
            ),
          }}
          style={{ flex: 1 }}
        />
        <StatisticCard
          statistic={{
            title: "阶段进度",
            value: "3/3",
            description: "全部阶段已交付",
            icon: (
              <CheckCircleOutlined style={{ color: "#52c41a", fontSize: 24 }} />
            ),
          }}
          style={{ flex: 1 }}
        />
      </StatisticCard.Group>

      {/* ─── 阶段一：MCP 中台 ─── */}
      <Card title="🔧 阶段一：MCP 中台底座" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          {stage1Projects.map((p) => (
            <Col key={p.title} span={8}>
              <ProjectCard {...p} />
            </Col>
          ))}
        </Row>
      </Card>

      {/* ─── 阶段二：B 端赋能 ─── */}
      <Card title="🏢 阶段二：B 端赋能工具" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          {stage2Projects.map((p) => (
            <Col key={p.title} span={8}>
              <ProjectCard {...p} />
            </Col>
          ))}
        </Row>
      </Card>

      {/* ─── 阶段三：C 端产品 ─── */}
      <Card title="📱 阶段三：C 端获客产品" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          {stage3Projects.map((p) => (
            <Col key={p.title} span={8}>
              <ProjectCard {...p} />
            </Col>
          ))}
        </Row>
      </Card>

      {/* ─── 前端入口 ─── */}
      <Card title="🌐 前端项目入口" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          {frontendProjects.map((p) => (
            <Col key={p.title} span={8}>
              <ProjectCard {...p} />
            </Col>
          ))}
        </Row>
      </Card>

      {/* ─── 快速操作 ─── */}
      <Card title="⚡ 快速操作" style={{ marginBottom: 24 }}>
        <Space wrap>
          <Button icon={<SunOutlined />} onClick={() => setTheme("light")}>
            亮色主题
          </Button>
          <Button icon={<MoonOutlined />} onClick={() => setTheme("dark")}>
            暗色主题
          </Button>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={toggleTheme}
          >
            切换主题
          </Button>
          <Button
            icon={<LinkOutlined />}
            onClick={() => window.open("http://localhost:8000", "_blank")}
          >
            MCP HUB
          </Button>
          <Button
            icon={<BugOutlined />}
            onClick={() =>
              window.open("http://localhost:5173/monitor", "_blank")
            }
          >
            服务监控
          </Button>
          <Button
            icon={<UserOutlined />}
            onClick={() => (window.location.href = "/user-profile")}
          >
            用户画像
          </Button>
        </Space>
      </Card>

      <Divider />
      <div style={{ textAlign: "center", color: "#bfbfbf", fontSize: 12 }}>
        康康 AI 全栈系统 · 阶段一 MCP 中台 + 阶段二 B 端赋能 + 阶段三 C 端产品 ·{" "}
        {new Date().getFullYear()}
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
      {
        path: "/quota",
        name: "配额管理",
        icon: <DatabaseOutlined />,
        routes: [
          { path: "/quota/dataOverview", name: "数据概览" },
          { path: "/quota/rules", name: "规则配置" },
        ],
      },
      { path: "/models", name: "模型管理", icon: <ExperimentOutlined /> },
      { path: "/data", name: "数据看板", icon: <DatabaseOutlined /> },
      { path: "/auth", name: "权限管理", icon: <SafetyOutlined /> },
      { path: "/monitor", name: "服务监控", icon: <MonitorOutlined /> },
      { path: "/data/annotation", name: "数据标注", icon: <EditOutlined /> },
      { path: "/prompts", name: "Prompt 管理", icon: <FileTextOutlined /> },
      { path: "/auth/keys", name: "API Key", icon: <KeyOutlined /> },
      { path: "/user-profile", name: "用户画像", icon: <UserOutlined /> },
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
        <div
          onClick={() => {
            const subRoutes = (
              item as unknown as { routes?: Array<{ path?: string }> }
            ).routes;
            if (subRoutes && subRoutes.length > 0) {
              // Parent menu: navigate to first child route
              navigate(subRoutes[0].path!);
            } else if (item.path) {
              navigate(item.path);
            }
          }}
        >
          {dom}
        </div>
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
        <Route path="/quota/dataOverview" element={<QuotaPage />} />
        <Route path="/quota/rules" element={<QuotaRulesPage />} />
        <Route path="/monitor" element={<MonitorPage />} />
        <Route path="/data/annotation" element={<AnnotationPage />} />
        <Route path="/prompts" element={<PromptsPage />} />
        <Route path="/auth/keys" element={<ApiKeysPage />} />
        <Route path="/user-profile" element={<UserProfilePage />} />
      </Routes>
    </ProLayout>
  );
}
