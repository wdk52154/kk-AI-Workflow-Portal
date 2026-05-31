import { useState } from "react";
import {
  Card,
  Input,
  Button,
  Table,
  Tag,
  message,
  Space,
  Alert,
  Select,
} from "antd";
import { SearchOutlined, UserOutlined } from "@ant-design/icons";

interface UserFact {
  fact_id: string;
  fact_type: string;
  fact_content: string;
  confidence: number;
  source_project_id: string;
  created_at: string;
}

const MEMORY_BASE = "http://localhost:9003";

async function recallUserFacts(
  userId: string,
  factType?: string,
  query?: string,
): Promise<{ user_id: string; total: number; facts: UserFact[] }> {
  const res = await fetch(`${MEMORY_BASE}/v1/recall_user_facts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      ...(factType ? { fact_type: factType } : {}),
      ...(query ? { query } : {}),
      top_k: 20,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || "查询失败");
  }
  return res.json();
}

export default function UserProfilePage() {
  const [userId, setUserId] = useState("");
  const [factType, setFactType] = useState<string | undefined>(undefined);
  const [semanticQuery, setSemanticQuery] = useState("");
  const [result, setResult] = useState<{
    user_id: string;
    total: number;
    facts: UserFact[];
  } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!userId.trim()) {
      message.warning("请输入 user_id");
      return;
    }
    setLoading(true);
    try {
      const res = await recallUserFacts(
        userId,
        factType,
        semanticQuery || undefined,
      );
      setResult(res);
    } catch (e: any) {
      message.error(e.message || "查询失败");
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: "事实类型",
      dataIndex: "fact_type",
      key: "fact_type",
      render: (t: string) => {
        const colorMap: Record<string, string> = {
          preference: "blue",
          constraint: "red",
          profile: "green",
          behavior: "orange",
        };
        return <Tag color={colorMap[t] || "default"}>{t}</Tag>;
      },
    },
    { title: "事实内容", dataIndex: "fact_content", key: "content" },
    {
      title: "置信度",
      dataIndex: "confidence",
      key: "confidence",
      render: (v: number) => `${Math.round(v * 100)}%`,
    },
    {
      title: "来源项目",
      dataIndex: "source_project_id",
      key: "source",
      render: (v: string) => <Tag>{v}</Tag>,
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
    },
  ];

  return (
    <div>
      <h2>
        <UserOutlined /> 用户画像查询（跨项目调试）
      </h2>
      <Card style={{ marginBottom: 16 }}>
        <Space wrap align="center">
          <Input.Search
            placeholder="输入 user_id"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            onSearch={handleSearch}
            style={{ width: 280 }}
            enterButton={<SearchOutlined />}
            loading={loading}
          />
          <Select
            placeholder="事实类型筛选"
            allowClear
            style={{ width: 150 }}
            value={factType}
            onChange={setFactType}
          >
            <Select.Option value="preference">偏好</Select.Option>
            <Select.Option value="constraint">约束</Select.Option>
            <Select.Option value="profile">画像</Select.Option>
            <Select.Option value="behavior">行为</Select.Option>
          </Select>
          <Input
            placeholder="语义查询（可选）"
            value={semanticQuery}
            onChange={(e) => setSemanticQuery(e.target.value)}
            style={{ width: 200 }}
          />
          <Button type="primary" onClick={handleSearch} loading={loading}>
            查询
          </Button>
        </Space>
      </Card>

      {result && (
        <>
          <Alert
            message={`用户 ${result.user_id} 共找到 ${result.total} 条事实记录`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Table
            dataSource={result.facts}
            columns={columns}
            rowKey="fact_id"
            pagination={{ pageSize: 10 }}
          />
        </>
      )}

      <Card title="调试说明" style={{ marginTop: 24 }}>
        <p>1. 输入 user_id 可查询该用户在所有项目中的画像事实。</p>
        <p>
          2. 支持按 fact_type
          筛选：preference（偏好）、constraint（约束）、profile（画像）、behavior（行为）。
        </p>
        <p>3. 语义查询会基于向量相似度召回最相关的事实。</p>
        <p>
          4. 测试场景：客服项目记录「用户对芒果过敏」→ 销售 Agent
          自动召回并规避含芒果成分的产品推荐。
        </p>
      </Card>
    </div>
  );
}
