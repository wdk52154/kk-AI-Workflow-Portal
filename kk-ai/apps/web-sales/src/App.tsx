import { Routes, Route } from "react-router-dom";
import { Layout, Menu, theme } from "antd";
import {
  DashboardOutlined,
  MessageOutlined,
  RobotOutlined,
  BookOutlined,
} from "@ant-design/icons";
import { useNavigate, useLocation } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import ScriptAssistant from "./pages/ScriptAssistant";
import RoleplayRoom from "./pages/RoleplayRoom";
import ScriptLibrary from "./pages/ScriptLibrary";

const { Header, Content, Sider } = Layout;

const items = [
  { key: "/", icon: <DashboardOutlined />, label: "销售看板" },
  { key: "/assistant", icon: <MessageOutlined />, label: "话术助手" },
  { key: "/roleplay", icon: <RobotOutlined />, label: "AI 陪练室" },
  { key: "/library", icon: <BookOutlined />, label: "话术库" },
];

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider theme="light" width={200}>
        <div style={{ padding: "16px", fontWeight: "bold", fontSize: 18 }}>
          销售智能 Agent
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={items}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: "0 24px", background: colorBgContainer }}>
          <h3 style={{ margin: 0 }}>康康 AI · 销售智能 Agent</h3>
        </Header>
        <Content
          style={{
            margin: 16,
            padding: 24,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            minHeight: "calc(100vh - 96px)",
          }}
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/assistant" element={<ScriptAssistant />} />
            <Route path="/roleplay" element={<RoleplayRoom />} />
            <Route path="/library" element={<ScriptLibrary />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
