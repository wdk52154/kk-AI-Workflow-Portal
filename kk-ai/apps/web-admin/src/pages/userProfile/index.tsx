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
  Form,
  Modal,
  Divider,
  Steps,
} from "antd";
import {
  SearchOutlined,
  UserOutlined,
  PlusOutlined,
  ExperimentOutlined,
  CheckCircleOutlined,
} from "@ant-design/icons";

interface UserFact {
  fact_id: string;
  fact_type: string;
  fact_content: string;
  confidence: number;
  source_project_id: string;
  created_at: string;
}

const MEMORY_BASE = "http://localhost:9003";
const SALES_BASE = "http://localhost:9007";

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

async function storeUserFact(data: {
  user_id: string;
  fact_type: string;
  fact_content: string;
  confidence: number;
  source_project_id: string;
}): Promise<{ fact_id: string }> {
  const res = await fetch(`${MEMORY_BASE}/v1/store_user_fact`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.message || "存储失败");
  }
  return res.json();
}

async function salesQuery(userId: string, question: string) {
  const res = await fetch(`${SALES_BASE}/v1/sales/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      customer_question: question,
      user_id: userId,
    }),
  });
  if (!res.ok) throw new Error("销售查询失败");
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

  // 写入事实
  const [writeOpen, setWriteOpen] = useState(false);
  const [writeForm] = Form.useForm();
  const [writeLoading, setWriteLoading] = useState(false);

  // 端到端验证
  const [verifyStep, setVerifyStep] = useState(0);
  const [verifyUserId, setVerifyUserId] = useState("user-demo-001");
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyResult, setVerifyResult] = useState<any>(null);

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

  const handleWrite = async () => {
    const values = writeForm.getFieldsValue();
    if (!values.user_id || !values.fact_content) {
      message.warning("请填写完整");
      return;
    }
    setWriteLoading(true);
    try {
      const res = await storeUserFact({
        user_id: values.user_id,
        fact_type: values.fact_type || "constraint",
        fact_content: values.fact_content,
        confidence: values.confidence || 0.95,
        source_project_id:
          values.source_project_id || "project-ai-customer-service",
      });
      message.success(`事实已存储: ${res.fact_id}`);
      setWriteOpen(false);
      writeForm.resetFields();
      // 如果写入的是当前查询的用户，自动刷新
      if (userId === values.user_id) handleSearch();
    } catch (e: any) {
      message.error(e.message || "存储失败");
    } finally {
      setWriteLoading(false);
    }
  };

  const runE2EVerification = async () => {
    setVerifyLoading(true);
    setVerifyStep(0);
    setVerifyResult(null);
    try {
      // Step 1: 项目1（AI客服）记录 "用户对芒果过敏"
      setVerifyStep(0);
      await storeUserFact({
        user_id: verifyUserId,
        fact_type: "constraint",
        fact_content: "用户对芒果过敏",
        confidence: 0.95,
        source_project_id: "project-ai-customer-service",
      });
      await new Promise((r) => setTimeout(r, 500));

      // Step 2: 项目4（销售Agent）召回该事实
      setVerifyStep(1);
      const recall = await recallUserFacts(verifyUserId);
      const hasAllergy = recall.facts.some(
        (f) =>
          f.fact_content.includes("芒果") && f.fact_content.includes("过敏"),
      );
      await new Promise((r) => setTimeout(r, 500));

      // Step 3: 销售查询，验证自动规避
      setVerifyStep(2);
      const salesRes = await salesQuery(
        verifyUserId,
        "我想买护肤品，有什么推荐？",
      );

      setVerifyResult({
        stored: true,
        recalled: hasAllergy,
        user_facts: salesRes.user_facts,
        objection_handler: salesRes.objection_handler,
        recommended_scripts: salesRes.recommended_scripts,
      });
      setVerifyStep(3);

      if (hasAllergy && salesRes.objection_handler) {
        message.success("端到端验证通过：客服记录 → 销售召回 → 自动规避");
      } else {
        message.warning("验证完成，但未触发自动规避（可能无相关话术）");
      }
    } catch (e: any) {
      message.error(e.message || "验证失败");
    } finally {
      setVerifyLoading(false);
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

      {/* 查询区域 */}
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
          <Button icon={<PlusOutlined />} onClick={() => setWriteOpen(true)}>
            写入事实
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

      <Divider />

      {/* 端到端验证 */}
      <Card
        title={
          <>
            <ExperimentOutlined /> 端到端验证：客服记录 → 销售召回 → 自动规避
          </>
        }
      >
        <Space direction="vertical" style={{ width: "100%" }}>
          <Input
            placeholder="验证用 user_id"
            value={verifyUserId}
            onChange={(e) => setVerifyUserId(e.target.value)}
            style={{ width: 300 }}
          />
          <Steps
            current={verifyStep}
            items={[
              {
                title: "客服记录",
                description: '存储 "用户对芒果过敏"',
              },
              { title: "销售召回", description: "查询用户画像事实" },
              { title: "自动规避", description: "销售推荐时过滤芒果产品" },
              {
                title: "验证完成",
                description: verifyResult
                  ? verifyResult.recalled
                    ? "✅ 跨项目画像生效"
                    : "⚠️ 未触发规避"
                  : "等待执行",
              },
            ]}
          />
          <Button
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={runE2EVerification}
            loading={verifyLoading}
          >
            运行端到端验证
          </Button>

          {verifyResult && (
            <Alert
              message={
                verifyResult.recalled && verifyResult.objection_handler
                  ? "✅ 验证通过：客服记录的事实已被销售 Agent 召回，并自动触发产品规避"
                  : verifyResult.recalled
                    ? "⚠️ 事实已召回，但未在销售推荐中触发规避（可能无相关产品）"
                    : "❌ 事实未成功召回"
              }
              type={
                verifyResult.recalled && verifyResult.objection_handler
                  ? "success"
                  : verifyResult.recalled
                    ? "warning"
                    : "error"
              }
              showIcon
            />
          )}
        </Space>
      </Card>

      {/* 写入事实 Modal */}
      <Modal
        title="写入用户画像事实"
        open={writeOpen}
        onOk={handleWrite}
        onCancel={() => setWriteOpen(false)}
        confirmLoading={writeLoading}
      >
        <Form form={writeForm} layout="vertical">
          <Form.Item
            name="user_id"
            label="用户 ID"
            rules={[{ required: true }]}
          >
            <Input placeholder="如：user-demo-001" />
          </Form.Item>
          <Form.Item
            name="fact_type"
            label="事实类型"
            initialValue="constraint"
          >
            <Select>
              <Select.Option value="preference">偏好</Select.Option>
              <Select.Option value="constraint">约束</Select.Option>
              <Select.Option value="profile">画像</Select.Option>
              <Select.Option value="behavior">行为</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="fact_content"
            label="事实内容"
            rules={[{ required: true }]}
          >
            <Input.TextArea rows={3} placeholder="如：用户对芒果过敏" />
          </Form.Item>
          <Form.Item
            name="source_project_id"
            label="来源项目"
            initialValue="project-ai-customer-service"
          >
            <Input placeholder="如：project-ai-customer-service" />
          </Form.Item>
          <Form.Item name="confidence" label="置信度" initialValue={0.95}>
            <Input type="number" max={1} min={0} step={0.01} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
