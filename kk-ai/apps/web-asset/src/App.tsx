import { Routes, Route } from "react-router-dom";
import { Layout, Menu, theme } from "antd";
import {
  DashboardOutlined,
  PictureOutlined,
  UploadOutlined,
  EditOutlined,
} from "@ant-design/icons";
import { useNavigate, useLocation } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import AssetLibrary from "./pages/AssetLibrary";
import AssetUpload from "./pages/AssetUpload";
import PosterEditor from "./pages/PosterEditor";

const { Header, Content, Sider } = Layout;

const items = [
  { key: "/", icon: <DashboardOutlined />, label: "运营看板" },
  { key: "/library", icon: <PictureOutlined />, label: "素材库" },
  { key: "/upload", icon: <UploadOutlined />, label: "上传素材" },
  { key: "/poster", icon: <EditOutlined />, label: "海报编辑器" },
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
          素材管理平台
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
          <h3 style={{ margin: 0 }}>康康 AI · 素材管理与运营平台</h3>
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
            <Route path="/library" element={<AssetLibrary />} />
            <Route path="/upload" element={<AssetUpload />} />
            <Route path="/poster" element={<PosterEditor />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
